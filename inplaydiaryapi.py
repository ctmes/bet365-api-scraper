import os
# curl_cffi impersonates a real browser's TLS/JA3 fingerprint so Cloudflare
# doesn't 403 us the way plain `requests` gets blocked.
from curl_cffi import requests
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class InPlays:
    def __init__(self):
        # Configura a URL da API e os cabeçalhos necessários para a solicitação
        self.api_url = os.getenv('INPLAYDIARYAPI')
        if not self.api_url:
            raise ValueError("INPLAYDIARYAPI URL must be set in the .env file")

        self.headers = {
            'Accept': os.getenv('ACCEPT'),
            'Accept-Encoding': os.getenv('ACCEPT_ENCODING'),
            'Accept-Language': os.getenv('ACCEPT_LANGUAGE'),
            'Cache-Control': os.getenv('CACHE_CONTROL'),
            'Connection': os.getenv('CONNECTION'),
            'Cookie': os.getenv('COOKIE'),
            'Host': os.getenv('HOST'),
            'Origin': os.getenv('ORIGIN'),
            'Pragma': os.getenv('PRAGMA'),
            'Referer': os.getenv('REFERER'),
            'Sec-Ch-Ua': os.getenv('SEC_CH_UA'),
            'Sec-Ch-Ua-Mobile': os.getenv('SEC_CH_UA_MOBILE'),
            'Sec-Ch-Ua-Platform': os.getenv('SEC_CH_UA_PLATFORM'),
            'Sec-Fetch-Dest': os.getenv('SEC_FETCH_DEST'),
            'Sec-Fetch-Mode': os.getenv('SEC_FETCH_MODE'),
            'Sec-Fetch-Site': os.getenv('SEC_FETCH_SITE'),
            'Sec-Fetch-User': os.getenv('SEC_FETCH_USER'),
            'Upgrade-Insecure-Requests': os.getenv('UPGRADE_INSECURE_REQUESTS'),
            'User-Agent': os.getenv('USER_AGENT'),
            'Sec-WebSocket-Extensions': os.getenv('HEADERS_SEC_WEBSOCKET_EXTENSIONS'),
            'Sec-WebSocket-Protocol': os.getenv('HEADERS_SEC_WEBSOCKET_PROTOCOL'),
            'Sec-WebSocket-Version': os.getenv('HEADERS_SEC_WEBSOCKET_VERSION'),
            # bet365 anti-bot / session-sync tokens (captured from a live browser request)
            'X-Net-Sync-Term': os.getenv('X_NET_SYNC_TERM'),
            'X-Request-Id': os.getenv('X_REQUEST_ID'),
        }
        # Remove headers that weren't set in .env so we don't send empty values
        self.headers = {k: v for k, v in self.headers.items() if v}
        # Browser to impersonate for the TLS/JA3 fingerprint. Should roughly
        # match the User-Agent in .env (e.g. a recent Chrome/Edge build).
        self.impersonate = os.getenv('IMPERSONATE', 'chrome')
        self.session = requests.Session()

    def on(self):
        print("Initiating request to bet365 API...")
        try:
            # Realiza a solicitação GET para a API
            response = self.session.get(
                self.api_url or "",
                headers=self.headers,
                timeout=60,
                impersonate=self.impersonate,
            )
            response.raise_for_status()  # Levanta um erro para códigos de status HTTP >= 400
            print("Received response from bet365 API.")

            records = self.parse(response.text)
            print(f"Data processed successfully ({len(records)} records).")
            return records
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            return None
        except requests.exceptions.ConnectionError as conn_err:
            print(f'Connection error occurred: {conn_err}')
            return None
        except requests.exceptions.Timeout as timeout_err:
            print(f'Timeout error occurred: {timeout_err}')
            return None
        except requests.exceptions.RequestException as req_err:
            print(f'Error occurred: {req_err}')
            return None

    @staticmethod
    def parse(text):
        """Parse bet365's pipe-delimited feed into a list of dicts.

        The feed is a series of records separated by '|'. Each record is
        'TYPE;KEY=VALUE;KEY=VALUE;...' (e.g. 'CL;ID=1;NA=Soccer;...').
        Returns a list like [{'type': 'CL', 'ID': '1', 'NA': 'Soccer', ...}, ...].
        """
        records = []
        for chunk in text.split('|'):
            chunk = chunk.strip()
            if not chunk:
                continue
            parts = chunk.split(';')
            record = {'type': parts[0]}
            for field in parts[1:]:
                if '=' in field:
                    key, value = field.split('=', 1)
                    record[key] = value
            records.append(record)
        return records

if __name__ == "__main__":
    # Executa o processo principal
    in_plays = InPlays()
    print("Starting inPlays process...")
    result = in_plays.on()
    print("Result:", result)
