#!/bin/bash

python -m cProfile -o output.file run_game.py

runsnake output.file
