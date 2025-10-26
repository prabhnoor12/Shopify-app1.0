import os
import subprocess


class NgrokManager:
    def __init__(self, port: int, authtoken: str = None):
        self.port = port
        self.authtoken = authtoken or os.getenv("NGROK_AUTHTOKEN")
        self.ngrok_path = os.getenv("NGROK_PATH", "ngrok")
        self.tunnel_url = None

    def set_authtoken(self):
        if self.authtoken:
            subprocess.run(
                [self.ngrok_path, "config", "add-authtoken", self.authtoken], check=True
            )

    def start_tunnel(self):
        self.set_authtoken()
        proc = subprocess.Popen(
            [self.ngrok_path, "http", str(self.port), "--log=stdout"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for line in proc.stdout:
            if "url=" in line:
                # Extract public URL from ngrok output
                self.tunnel_url = line.split("url=")[1].split()[0]
                break
        return self.tunnel_url

    def stop_tunnel(self):
        subprocess.run([self.ngrok_path, "kill"], check=True)


# Example usage:
# ngrok = NgrokManager(port=8000, authtoken="your-ngrok-authtoken")
# public_url = ngrok.start_tunnel()
# print(f"Ngrok tunnel started at: {public_url}")
# ngrok.stop_tunnel()
