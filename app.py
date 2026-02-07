import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, flash
import yt_dlp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'kris-secret-key-123')

# --- UI TEMPLATE (Flowbite + Tailwind + Glassmorphism) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kris Downloader | All-in-One</title>
    <!-- Flowbite & Tailwind -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/flowbite/2.3.0/flowbite.min.css" rel="stylesheet" />
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        primary: {"50":"#eff6ff","100":"#dbeafe","200":"#bfdbfe","300":"#93c5fd","400":"#60a5fa","500":"#3b82f6","600":"#2563eb","700":"#1d4ed8","800":"#1e40af","900":"#1e3a8a","950":"#172554"}
                    }
                }
            }
        }
    </script>
    <style>
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        @keyframes gradient-xy {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .animate-float { animation: float 6s ease-in-out infinite; }
        .bg-animated {
            background: linear-gradient(-45deg, #0f172a, #1e1b4b, #312e81, #1e3a8a);
            background-size: 400% 400%;
            animation: gradient-xy 15s ease infinite;
        }
        .glass-panel {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body class="bg-animated min-h-screen flex flex-col items-center justify-center p-4 font-sans antialiased text-white selection:bg-blue-500 selection:text-white">

    <!-- Main Card -->
    <div class="glass-panel w-full max-w-2xl rounded-3xl shadow-2xl overflow-hidden relative animate-float">
        
        <!-- Decoration -->
        <div class="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>

        <div class="p-8 md:p-12">
            <!-- Header -->
            <div class="text-center mb-10">
                <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-600/20 mb-4 ring-1 ring-blue-500/50 shadow-[0_0_20px_rgba(37,99,235,0.3)]">
                    <svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                    </svg>
                </div>
                <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight mb-2">
                    Kris <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">Downloader</span>
                </h1>
                <p class="text-gray-400 text-lg">Universal Media Saver</p>
            </div>

            <!-- Error Messages -->
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="flex items-center p-4 mb-6 text-sm text-red-400 rounded-xl bg-red-900/20 border border-red-900/50" role="alert">
                            <svg class="flex-shrink-0 inline w-4 h-4 me-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z"/>
                            </svg>
                            <span class="sr-only">Info</span>
                            <div>{{ message }}</div>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <!-- Form -->
            <form action="/get-link" method="POST" class="space-y-6" onsubmit="document.getElementById('btn-text').classList.add('hidden'); document.getElementById('btn-loader').classList.remove('hidden');">
                <div class="relative group">
                    <div class="absolute inset-y-0 start-0 flex items-center ps-4 pointer-events-none">
                        <svg class="w-5 h-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20">
                            <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 19l-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z"/>
                        </svg>
                    </div>
                    <input type="url" name="url" id="url" class="block w-full p-5 ps-12 text-sm text-white bg-gray-900/50 border border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-500 transition-all shadow-inner" placeholder="Paste TikTok, YouTube, or Instagram link..." required>
                </div>

                <button type="submit" class="w-full group relative flex justify-center py-4 px-4 border border-transparent text-sm font-bold rounded-xl text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-blue-500 transition-all shadow-lg hover:shadow-blue-500/25">
                    <span id="btn-text" class="text-lg">Download Now</span>
                    <span id="btn-loader" class="hidden flex items-center">
                        <svg aria-hidden="true" role="status" class="inline w-6 h-6 me-3 text-white animate-spin" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="#E5E7EB"/>
                            <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentColor"/>
                        </svg>
                        Processing...
                    </span>
                </button>
            </form>

            <!-- Supported Platforms -->
            <div class="mt-10 grid grid-cols-3 gap-4">
                <div class="flex flex-col items-center justify-center p-4 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
                    <svg class="w-8 h-8 text-red-500 mb-2" fill="currentColor" viewBox="0 0 24 24"><path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/></svg>
                    <span class="text-xs font-bold text-gray-300">YouTube</span>
                </div>
                <div class="flex flex-col items-center justify-center p-4 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
                    <svg class="w-8 h-8 text-pink-500 mb-2" fill="currentColor" viewBox="0 0 24 24"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/></svg>
                    <span class="text-xs font-bold text-gray-300">TikTok</span>
                </div>
                <div class="flex flex-col items-center justify-center p-4 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
                    <svg class="w-8 h-8 text-purple-500 mb-2" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
                    <span class="text-xs font-bold text-gray-300">Instagram</span>
                </div>
            </div>
            
            <footer class="mt-12 text-center">
                <p class="text-sm text-gray-500">© 2026 Kris Panel. Powered by Python.</p>
            </footer>
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/flowbite/2.3.0/flowbite.min.js"></script>
</body>
</html>
"""

# --- BACKEND LOGIC ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def cobalt_fallback(url):
    """
    Fallback method using the public Cobalt API when yt-dlp fails.
    This guarantees a result even if YouTube blocks the server IP.
    """
    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        # Using a public cobalt instance (you can swap this URL if needed)
        api_url = "https://api.cobalt.tools/api/json"
        data = {
            "url": url,
            "vQuality": "1080"
        }
        
        response = requests.post(api_url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            # Cobalt returns 'url' for direct link or 'picker' sometimes
            if 'url' in result:
                return result['url']
            elif 'picker' in result and result['picker']:
                return result['picker'][0]['url']
                
        return None
    except Exception as e:
        print(f"Cobalt fallback failed: {e}")
        return None

@app.route('/get-link', methods=['POST'])
def get_link():
    url = request.form.get('url')
    if not url:
        flash("Please enter a valid URL.")
        return redirect(url_for('index'))

    # 1. Attempt using yt-dlp with anti-bot headers
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
        'forceurl': True,
        'skip_download': True,
        'noplaylist': True,
        # ANTI-BOT CONFIGURATION
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android']  # Mimic mobile apps to bypass web bot checks
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # We wrap this in a broader try/except because 'extract_info' is where it usually crashes
            try:
                info = ydl.extract_info(url, download=False)
                
                # Handling generic direct URL or specific formats
                download_link = None
                if info:
                    if 'url' in info:
                        download_link = info['url']
                    elif 'entries' in info:
                        download_link = info['entries'][0]['url']
                
                if download_link:
                    return redirect(download_link)
                    
            except Exception as inner_e:
                # yt-dlp failed (likely the "Sign in" error), trigger fallback
                print(f"yt-dlp error: {inner_e}. Switching to fallback...")
                pass # Fall through to Cobalt
                
    except Exception as e:
        print(f"General error: {e}")

    # 2. FALLBACK: If yt-dlp failed (or blocked), use Cobalt API
    fallback_link = cobalt_fallback(url)
    if fallback_link:
        return redirect(fallback_link)

    # 3. If everything fails
    flash("Server busy or blocked. Please try again later.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
