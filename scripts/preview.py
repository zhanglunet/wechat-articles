#!/usr/bin/env python3
"""Push a WeChat draft preview to one user by WeChat ID.

Uses the official mass preview API (message/mass/preview) with
mpnews + towxname. Sends only to the given WeChat ID, never a mass send.

Usage:
    python3 scripts/preview.py <draft media_id> <recipient WeChat ID>
    python3 scripts/preview.py <draft media_id> <recipient WeChat ID> --config ~/.config/md2wechat/config.yaml

The config file holds wechat.appid / wechat.secret and is never committed
(it is gitignored). This script carries no credential, no media_id and no
WeChat ID of its own; both identifiers come from the command line each run.

Prints only the preview API result (msg_id on success, errcode on failure).
Never prints credentials or the access token.
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request


def read_config(path):
    appid = secret = None
    in_wechat = False
    for line in open(path, encoding="utf-8"):
        stripped = line.strip()
        if stripped == "wechat:":
            in_wechat = True
            continue
        if in_wechat:
            if line.strip() and not line.startswith((" ", "\t")):
                break
            key, sep, val = stripped.partition(":")
            if not sep:
                continue
            val = val.strip()
            if key == "appid":
                appid = val
            elif key == "secret":
                secret = val
    return appid, secret


def get_json(url, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media_id", help="draft media_id from test-draft / create_draft")
    parser.add_argument("towxname", help="recipient WeChat ID (towxname)")
    parser.add_argument(
        "--config",
        default="~/.config/md2wechat/config.yaml",
        help="md2wechat config file with wechat.appid / wechat.secret",
    )
    args = parser.parse_args()

    appid, credential = read_config(os.path.expanduser(args.config))
    if not appid or not credential:
        print("CONFIG_MISSING")
        sys.exit(1)

    query = urllib.parse.urlencode(
        [
            ("grant_type", "client_credential"),
            ("appid", appid),
            ("secret", credential),
        ]
    )
    tok = get_json("https://api.weixin.qq.com/cgi-bin/token?" + query)
    if "access_token" not in tok:
        print("TOKEN_FAILED", json.dumps(tok, ensure_ascii=False))
        sys.exit(1)

    res = get_json(
        "https://api.weixin.qq.com/cgi-bin/message/mass/preview"
        f"?access_token={tok['access_token']}",
        {"towxname": args.towxname, "msgtype": "mpnews", "mpnews": {"media_id": args.media_id}},
    )
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
