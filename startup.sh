# place these lines of code in rc.local in order to run at startup on the pi

# move to the cocwifi directory
cd /home/pi/code/cocwifi/

# start the coc wifi web and ftp servers
# sudo python run.py >weblog.log 2>&1 &
sudo python initdb.py
sudo gunicorn --workers 2 --log-file gunicornlog.log --log-level debug -p gunicorn.pid -b 0.0.0.0:80 coc_wifiscoring:app
sudo python ftpserver.py >ftplog.log 2>&1 &