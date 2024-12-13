#!/bin/bash

sphinx-apidoc -o source/ ../crypto/hsecrypto
sphinx-apidoc -o source/ ../server/hseserver
sphinx-apidoc -o source/ ../client/hseclient

make html