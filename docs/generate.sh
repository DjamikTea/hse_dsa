#!/bin/bash

sphinx-apidoc -o source/ ../crypto/hsecrypto
sphinx-apidoc -o source/ ../server
sphinx-apidoc -o source/ ../client

make html