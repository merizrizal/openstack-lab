cd octavia/bin/
source create_dual_intermediate_CA.sh
mkdir -p /etc/octavia/certs/private
chmod 755 /etc/octavia -R
cp -p etc/octavia/certs/server_ca.cert.pem /etc/octavia/certs
cp -p etc/octavia/certs/server_ca-chain.cert.pem /etc/octavia/certs
cp -p etc/octavia/certs/server_ca.key.pem /etc/octavia/certs/private
cp -p etc/octavia/certs/client_ca.cert.pem /etc/octavia/certs
cp -p etc/octavia/certs/client.cert-and-key.pem /etc/octavia/certs/private
sudo chown -R octavia:octavia /etc/octavia