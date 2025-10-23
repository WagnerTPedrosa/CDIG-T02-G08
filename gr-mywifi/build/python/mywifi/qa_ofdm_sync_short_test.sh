#!/usr/bin/sh
export VOLK_GENERIC=1
export GR_DONT_LOAD_PREFS=1
export srcdir=/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi
export GR_CONF_CONTROLPORT_ON=False
export PATH="/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/build/python/mywifi":"$PATH"
export LD_LIBRARY_PATH="":$LD_LIBRARY_PATH
export PYTHONPATH=/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/build/test_modules:$PYTHONPATH
/usr/bin/python3 /home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/qa_ofdm_sync_short.py 
