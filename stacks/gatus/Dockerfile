# Upstream Gatus is `scratch`: no shell, no wget, and a fresh volume is root-owned (ADR 0013).
FROM busybox:1.37.0-musl AS bb
RUN mkdir /data && chown 1001:1001 /data
FROM ghcr.io/twin/gatus:v5.37.0
COPY --from=bb /bin/busybox /busybox/busybox
COPY --from=bb --chown=1001:1001 /data /data
USER 1001
