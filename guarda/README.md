# Guarda service for ExaBGP

## As root

Edit guarda.service file and set correct location of guarda.py. 

Then edit guarda.py and set address of your host.


```bash
pip install requests
chmod +x guarda.py
cp guarda.service /usr/lib/systemd/system/guarda.service
systemctl start guarda.service
systemctl enable guarda.service
```
