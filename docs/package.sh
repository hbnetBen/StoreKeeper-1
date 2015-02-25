#!/bin/bash -e

function do_install()
{
    make html
}

function do_start()
{
    xdg-open _build/html/index.html
}

function do_clear()
{
    if [ -e _build ]
    then
        rm -rf _build
    fi
}


cd "$(dirname "$0")"
source ../.main.sh