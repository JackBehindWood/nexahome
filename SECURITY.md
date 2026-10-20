# Security Policy

## Reporting a vulnerability

Please report security issues privately using GitHub's "Report a vulnerability" feature on this repository (Security tab). Do not open a public issue for a vulnerability.

## What must never be committed

Passwords, API keys, tokens, private keys, live databases, `.env` files, and personal data (names, hostnames, IP addresses, emails). Use `.env.example` with placeholders. If you believe a secret was committed, treat it as compromised: rotate it first, then report it.

## Deployment guidance

Keep administrative interfaces off the public internet; use a local network or VPN. Published container ports bind to `127.0.0.1` by default.
