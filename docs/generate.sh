#!/bin/bash

sphinx-apidoc -o source/ ../crypto/hsecrypto
sphinx-apidoc -o source/ ../server

make html