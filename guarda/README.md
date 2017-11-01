#Guarda service for ExaBGP

## As root

pip install requests
chmod +x guarda.py
cp guarda.service /usr/lib/systemd/system/guarda.service
systemctl start guarda.service
systemctl enable guarda.service