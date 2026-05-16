python-vipaccess
================

[![PyPI](https://img.shields.io/pypi/v/python-vipaccess.svg)](https://pypi.python.org/pypi/python-vipaccess)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build Status](https://github.com/cnDelbert/python-vipaccess/workflows/test_and_release/badge.svg)](https://github.com/cnDelbert/python-vipaccess/actions?query=workflow%3Atest_and_release)

Table of Contents
=================

* [python-vipaccess](#python-vipaccess)
* [Table of Contents](#table-of-contents)
   * [Intro](#intro)
   * [Dependencies](#dependencies)
   * [Installation](#installation)
      * [从 PyPI 安装（推荐）](#从-pypi-安装推荐)
      * [使用 uv（开发推荐）](#使用-uv开发推荐)
   * [Usage](#usage)
      * [Provisioning a new VIP Access credential](#provisioning-a-new-vip-access-credential)
      * [Display a QR code to register your credential with mobile TOTP apps](#display-a-qr-code-to-register-your-credential-with-mobile-totp-apps)
      * [Generating access codes using an existing credential](#generating-access-codes-using-an-existing-credential)

This is a fork of [**`cyrozap/python-vipaccess`**](https://github.com/cnDelbert/python-vipaccess). Main differences:

- No dependency on `qrcode` or `image` libraries; you can easily use
  external tools such as [`qrencode`](https://github.com/fukuchi/libqrencode)
  to convert an `otpauth://` URI to a QR code if needed, so it seems
  unnecessary to build in this functionality.
- Option to generate either the mobile (`SYMC`/`VSMT`) or desktop (`SYDC`/`VSST`)
  versions of the VIP Access tokens; as far as I can tell there is no
  real difference between them, but some clients require one or the
  other specifically. There are also some rarer token types/prefixes
  which can be generated if necessary
  ([reference list from Symantec](https://support.symantec.com/us/en/article.tech239895.html))
- Command-line utility is expanded to support *both* token
  provisioning (creating a new token) and emitting codes for an
  existing token (inspired by the command-line interface of
  [`stoken`](https://github.com/cernekee/stoken), which handles the same functions for [RSA SecurID](https://en.wikipedia.org/wiki/RSA_SecurID) tokens

Intro
-----

python-vipaccess is a free and open source software (FOSS)
implementation of Symantec's VIP Access client (now owned by Broadcom).

If you need to access a network which uses VIP Access for [two-factor
authentication](https://en.wikipedia.org/wiki/Two-factor_authentication),
but can't or don't want to use Symantec's proprietary
applications—which are only available for Windows, MacOS, Android,
iOS—then this is for you.

As [@cyrozap](https://github.com/cyrozap) discovered in reverse-engineering the VIP Access protocol
([original blog
post](https://www.cyrozap.com/2014/09/29/reversing-the-symantec-vip-access-provisioning-protocol)),
Symantec VIP Access actually uses a **completely open standard**
called [Time-based One-time Password
Algorithm](https://en.wikipedia.org/wiki/Time-based_One-time_Password_Algorithm)
for generating the 6-digit codes that it outputs. The only
non-standard part is the **provisioning** protocol used to create a
new token.

Dependencies
------------

-  Python 3.9+
-  [`pycryptodome`](https://pypi.python.org/pypi/pycryptodome/3.19)
-  [`oath`](https://pypi.python.org/pypi/oath/1.4.2)
-  [`requests`](https://pypi.python.org/pypi/requests/2.31)
-  [`qrcode`](https://pypi.python.org/pypi/qrcode/) (optional, for QR code display)

Installation
------------

### 从 PyPI 安装（推荐）

使用 [`pip`](https://pip.pypa.io/en/stable/installing/) 安装：

```bash
# 安装最新发布版本
pip3 install python-vipaccess

# 安装并支持 QR 码显示
pip3 install python-vipaccess[qr]

# 安装并支持 PIL QR 码
pip3 install python-vipaccess[qr-pil]

# 安装最新开发版本
pip3 install https://github.com/cnDelbert/python-vipaccess/archive/HEAD.zip
```

### 使用 uv（开发推荐）

[`uv`](https://docs.astral.sh/uv/) 是一个快速的 Python 包管理器，适合开发和测试。

```bash
# 克隆仓库
git clone https://github.com/cnDelbert/python-vipaccess.git
cd python-vipaccess

# 创建虚拟环境并安装依赖
uv venv
uv pip install -e .

# 运行（方式一：已安装项目）
uv run vipaccess --help

# 运行（方式二：直接运行模块，无需安装）
uv run python -m vipaccess --help

# 安装并支持 QR 码显示
uv pip install -e ".[qr]"
```

**uv 常用命令对照：**

| pip 命令 | uv 命令 |
|---------|--------|
| `pip install -r requirements.txt` | `uv pip install -r requirements.txt` |
| `pip install -e .` | `uv pip install -e .` |
| `pip install package` | `uv pip install package` |
| `python -m vipaccess` | `uv run python -m vipaccess` |

Usage
-----

### Provisioning a new VIP Access credential

This is used to create a new VIP Access token. It connects to https://services.vip.symantec.com/prov
and requests a new token, then deobfuscates it, and checks whether it is properly decoded and
working correctly, via a second request to https://vip.symantec.com/otpCheck.

By default it stores the new token in the file `.vipaccess` in your home directory (in a
format similar to `stoken`), but it can store to another file instead,
or instead just print out the "token secret" string with instructions
about how to use it.

```
usage: vipaccess provision [-h] [-p | -o DOTFILE] [-t TOKEN_MODEL]

optional arguments:
  -h, --help            show this help message and exit
  -p, --print           Print the new credential, but don't save it to a file
  -o DOTFILE, --dotfile DOTFILE
                        File in which to store the new credential (default
                        ~/.vipaccess)
  -i ISSUER, --issuer ISSUER
                        Specify the issuer name to use (default: Symantec)
  -t TOKEN_MODEL, --token-model TOKEN_MODEL
                        VIP Access token model. Often SYMC/VSMT ("mobile"
                        token, default) or SYDC/VSST ("desktop" token). Some
                        clients only accept one or the other. Other more
                        obscure token types also exist:
                        https://support.symantec.com/en_US/article.TECH239895.html
```

Here is an example of the output from `vipaccess provision -p`:

```
Generating request...
Fetching provisioning response from Symantec server...
Getting token from response...
Decrypting token...
Checking token against Symantec server...
Credential created successfully:
	otpauth://totp/VIP%20Access:SYMC12345678?secret=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&issuer=Symantec&algorithm=SHA1&digits=6
This credential expires on this date: 2019-01-15T12:00:00.000Z

You will need the ID to register this credential: SYMC12345678

You can use oathtool to generate the same OTP codes
as would be produced by the official VIP Access apps:

    oathtool    -b --totp AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA  # output one code
    oathtool -v -b --totp AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA  # ... with extra information
```

Here is the format of the `.vipaccess` token file output from
`vipaccess provision [-o ~/.vipaccess]`. (This file is created with
read/write permissions *only* for the current user.)

```
version 1
secret AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
id SYMC12345678
expiry 2019-01-15T12:00:00.000Z
```

### Display a QR code to register your credential with mobile TOTP apps

Once you generate a token with `vipaccess provision`, use `vipaccess uri` to show the `otpauth://` URI and
display it as a QR code:

```bash
# 安装并支持 QR 码（pip）
pip3 install python-vipaccess[qr]

# 或使用 uv
uv pip install ".[qr]"

# 然后运行 uri 命令
vipaccess uri
# 或
uv run vipaccess uri
```

The system will automatically:
1. Try to use the `qrcode` Python library (if installed)
2. Fall back to `qrencode` command line tool (if available)
3. Display the URI as plain text (if neither is available)

Scan the code into your TOTP generating app,
like [FreeOTP](https://freeotp.github.io/) or
[Google Authenticator](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2).

### Generating access codes using an existing credential

The `vipaccess [show]` option will also do this for you: by default it
generates codes based on the credential in `~/.vipaccess`, but you can
specify an alternative credential file or specify the OATH "token
secret" on the command line.

```
usage: vipaccess show [-h] [-s SECRET | -f DOTFILE]

optional arguments:
  -h, --help            show this help message and exit
  -s SECRET, --secret SECRET
                        Specify the token secret on the command line (base32
                        encoded)
  -f DOTFILE, --dotfile DOTFILE
                        File in which the credential is stored (default
                        ~/.vipaccess
```

As alluded to above, you can use other standard
[OATH](https://en.wikipedia.org/wiki/Initiative_For_Open_Authentication)-based
tools to generate the 6-digit codes identical to what Symantec's official
apps produce.
