#!/bin/sh
# Read-only checks of what is running (make smoke). Never starts, stops or changes anything and
# never reads a .env file: domain and port come from the running edge container.
#   VERBOSE=1  show the evidence behind each ok line (paste it into the session log)
#   WAIT=60    retry for up to 60 seconds until everything passes (after a start or stop)
# Exit code 0 = all ok, 1 = at least one FAIL, 2 = nothing to check.
set -u
VERBOSE=${VERBOSE:-0}
WAIT=${WAIT:-0}
PREFIX=nexahome-

ok() { printf 'ok    %s\n' "$1"; if [ "$VERBOSE" = 1 ] && [ -n "${2:-}" ]; then printf '        %s\n' "$2"; fi; }
bad() { printf 'FAIL  %s: %s\n' "$1" "$2"; fails=$((fails + 1)); }
env_of() { docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$1" | sed -n "s/^$2=//p"; }

# Hosts (the part before .<domain>) listed one per line, sorted.
repo_hosts() {
	sed -n 's|^http://\([a-z0-9-]*\)\.{\$NEXAHOME_DOMAIN}.*|\1|p' stacks/edge/Caddyfile | sort -u
}
tile_hosts() {
	sed -n 's|.*href: http://\([a-z0-9-]*\)\.{{HOMEPAGE_VAR_DOMAIN}}.*|\1|p' stacks/portal/config/services.yaml | sort -u
}

# Remote addresses of established TCP connections that are not private (needs cat in the image).
outbound() {
	docker exec "$1" cat /proc/net/tcp /proc/net/tcp6 2>/dev/null | awk '
	function hex(s,  i, n) { n = 0; for (i = 1; i <= length(s); i++) n = n * 16 + index("0123456789ABCDEF", substr(s, i, 1)) - 1; return n }
	$4 == "01" {
		split($3, a, ":"); r = a[1]
		if (length(r) == 32) {
			if (r == "00000000000000000000000001000000") next
			if (substr(r, 1, 24) != "0000000000000000FFFF0000") { print "ipv6 " r; next }
			r = substr(r, 25)
		}
		o4 = hex(substr(r, 7, 2)); o3 = hex(substr(r, 5, 2))  # little-endian: last pair is the first octet
		if (o4 == 10 || o4 == 127 || (o4 == 172 && o3 >= 16 && o3 <= 31) || (o4 == 192 && o3 == 168)) next
		print o4 "." o3 ".x.x"
	}'
}

run() {
	fails=0
	tmp=$(mktemp)
	trap 'rm -f "$tmp"' EXIT
	ids=$(docker ps -q --filter label=com.docker.compose.project 2>/dev/null) || { echo "no container runtime running (start it as in the README)"; return 2; }
	[ -n "$ids" ] || { echo "no stacks are running"; return 2; }

	# 1 and 2: every running NexaHome container: health, restarts, and what actually runs.
	edge=""
	for id in $ids; do
		line=$(docker inspect --format '{{.Name}}|{{index .Config.Labels "com.docker.compose.project"}}|{{.Config.User}}|{{.HostConfig.ReadonlyRootfs}}|{{.HostConfig.CapDrop}}|{{.HostConfig.CapAdd}}|{{with .State.Health}}{{.Status}}{{end}}|{{.RestartCount}}|{{range .Mounts}}{{.Source}} {{end}}|{{range $p, $b := .HostConfig.PortBindings}}{{range $b}}{{if .HostIp}}{{.HostIp}}{{else}}ANY{{end}} {{end}}{{end}}' "$id")
		name=${line%%|*}; name=${name#/}; rest=${line#*|}
		project=${rest%%|*}; rest=${rest#*|}
		case "$project" in "$PREFIX"*) ;; *) continue ;; esac
		user=${rest%%|*}; rest=${rest#*|}
		rofs=${rest%%|*}; rest=${rest#*|}
		capdrop=${rest%%|*}; rest=${rest#*|}
		capadd=${rest%%|*}; rest=${rest#*|}
		health=${rest%%|*}; rest=${rest#*|}
		restarts=${rest%%|*}; rest=${rest#*|}
		mounts=${rest%%|*}; ports=${rest#*|}
		stack=${project#"$PREFIX"}
		[ "$stack" = edge ] && edge=$id
		if [ "$health" = healthy ]; then ok "$stack healthy" "$name, restarts $restarts"
		else bad "$stack health" "${health:-no healthcheck}. logs: $(docker logs --tail 3 "$id" 2>&1 | tr '\n' ' ')"; fi
		[ "$restarts" = 0 ] || bad "$stack restarts" "$restarts (see docker logs $name)"
		problems=""
		case "$user" in ""|0|root|0:*|root:*) problems="$problems runs as root;" ;; esac
		[ "$rofs" = true ] || problems="$problems root filesystem writable;"
		case "$capdrop" in *ALL*) ;; *) problems="$problems capabilities not dropped;" ;; esac
		case "$capadd" in "[]"|"<no value>"|"[NET_BIND_SERVICE]"|"[CAP_NET_BIND_SERVICE]") ;; *) problems="$problems cap_add $capadd;" ;; esac
		case "$mounts" in *docker.sock*) problems="$problems Docker socket mounted;" ;; esac
		for h in $ports; do [ "$h" = 127.0.0.1 ] || problems="$problems port on '$h';"; done
		if [ -n "$problems" ]; then bad "$stack hardening" "$problems"
		else ok "$stack hardening" "user $user, read-only, cap_drop $capdrop, cap_add $capadd, ports on ${ports:-none}"; fi
		case "$stack" in edge|identity|portal)
			out=$(outbound "$id")
			if [ -n "$out" ]; then bad "$stack outbound" "established to $(echo "$out" | tr '\n' ' ')"
			elif ! docker exec "$id" cat /proc/net/tcp >/dev/null 2>&1; then ok "$stack outbound" "not inspectable (no tools in the image)"
			else ok "$stack outbound" "no non-private established connections"; fi ;;
		esac
	done
	[ -n "$edge" ] || { bad "edge" "not running; named URLs and the portal are unreachable. fix: make up STACK=edge"; return 1; }

	domain=$(env_of "$edge" NEXAHOME_DOMAIN); port=$(env_of "$edge" EDGE_PORT)
	base="$domain:$port"

	# 4: edge behaviour.
	[ "$(curl -s --max-time 5 http://127.0.0.1:"$port"/health)" = ok ] && ok "edge /health" || bad "edge /health" "no 'ok' on 127.0.0.1:$port"
	code=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' -H 'Host: other.example' http://127.0.0.1:"$port"/)
	[ "$code" = 404 ] && ok "edge foreign Host" "404" || bad "edge foreign Host" "got $code, want 404"

	# 3: the four-step contract, live: edge aliases, Caddyfile blocks, portal tiles.
	aliases=$(docker inspect --format '{{range $k, $v := .NetworkSettings.Networks}}{{range $v.Aliases}}{{println .}}{{end}}{{end}}' "$edge" | sed -n "s/\\.$domain\$//p" | sort -u)
	blocks=$(repo_hosts); tiles=$(tile_hosts)
	drift=""
	for h in $aliases; do
		echo "$blocks" | grep -qx "$h" || drift="$drift $h.(alias without Caddyfile block: step 2);"
		[ "$h" = home ] || echo "$tiles" | grep -qx "$h" || drift="$drift $h.(alias without tile: step 4);"
	done
	for h in $blocks; do echo "$aliases" | grep -qx "$h" || drift="$drift $h.(Caddyfile block without alias: step 1);"; done
	for h in $tiles; do echo "$aliases" | grep -qx "$h" || drift="$drift $h.(tile without alias: step 1);"; done
	if [ -n "$drift" ]; then bad "contract (add-a-stack steps)" "$drift"
	else ok "contract (add-a-stack steps)" "aliases = blocks = tiles: $(echo $aliases)"; fi

	for h in $aliases; do
		code=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' "http://$h.$base/")
		case "$code" in 000|404|502|503|504) bad "named URL $h" "http $code. fix: is the stack running and on the network?" ;; *) ok "named URL $h" "http $code" ;; esac
	done
	hdr=$(curl -sI --max-time 5 "http://id.$base/")
	echo "$hdr" | grep -qi 'x-content-type-options: nosniff' && echo "$hdr" | grep -qi 'x-frame-options: deny' && ok "edge headers" "nosniff, X-Frame-Options DENY" || bad "edge headers" "hardening headers missing"

	# 5: portal page.
	page=$(curl -s --max-time 10 "http://home.$base/")
	if [ -z "$page" ]; then bad "portal page" "empty. fix: make up STACK=portal"
	else
		# Tiles are rendered in the browser, so also read the config (what the portal will fetch) and /api/services.
		ext=$({ echo "$page" | grep -oE '(src|href)="https?://[^"]*"'; grep -hE 'https?://' stacks/portal/config/*.yaml | grep -v '^[[:space:]]*#' | grep -v HOMEPAGE_VAR_DOMAIN; } | grep -v "$domain" | head -3)
		sec=$({ echo "$page"; curl -s --max-time 10 "http://home.$base/api/services"; } | grep -ioE '(client_secret|api[_-]?key|password|bearer|token)[^<"]{0,20}' | head -3)
		[ -z "$ext" ] && ok "portal remote assets" "none in the page" || bad "portal remote assets" "$ext"
		[ -z "$sec" ] && ok "portal secrets" "none in the page" || bad "portal secrets" "$sec"
	fi
	# Each tile's dot (the portal's own monitor result) must agree with the named URL.
	tilelist=$(awk '/^- .*:$/ { g = $0; sub(/^- /, "", g); sub(/:$/, "", g) } /^    - .*:$/ { n = $0; sub(/^    - /, "", n); sub(/:$/, "", n); print g "|" n }' stacks/portal/config/services.yaml)
	echo "$tilelist" | while IFS='|' read -r g n; do
		[ -n "$n" ] || continue
		st=$(curl -s --max-time 10 --get --data-urlencode "groupName=$g" --data-urlencode "serviceName=$n" "http://home.$base/api/siteMonitor" | sed -n 's/.*"status":\([0-9]*\).*/\1/p')
		echo "TILE|$n|${st:-none}"
	done > "$tmp"
	while IFS='|' read -r _ n st; do
		case "$st" in 200|2??|3??) ok "tile dot $n" "monitor status $st" ;; *) bad "tile dot $n" "monitor status ${st:-none} (red). fix: is the stack running and on the edge?" ;; esac
	done < "$tmp"
	return $((fails > 0))
}

start=$(date +%s)
while :; do
	out=$(run); rc=$?
	[ "$rc" = 0 ] && break
	[ "$rc" = 2 ] && break
	[ $(($(date +%s) - start)) -ge "$WAIT" ] && break
	sleep 3
done
echo "$out"
case $rc in
	0) echo "smoke: all checks passed" ;;
	2) echo "smoke: nothing to check" ;;
	*) echo "smoke: $(echo "$out" | grep -c '^FAIL') check(s) failed" ;;
esac
exit $rc
