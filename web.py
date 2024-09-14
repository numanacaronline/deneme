from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory, jsonify
import os
import yt_dlp
import threading

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'downloads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def download_video(url, format, output_dir, progress_callback):
    ydl_opts = {
        'format': format,
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'progress_hooks': [lambda d: progress_callback(d)]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Social Media Video Downloader</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-100 flex flex-col items-center justify-center min-h-screen">
            <div class="max-w-md w-full bg-white p-6 rounded-lg shadow-md">
                <h1 class="text-2xl font-bold mb-4 text-center">Video Downloader</h1>
                <form id="download-form" action="/download" method="post" class="space-y-4">
                    <div>
                        <label for="url" class="block text-gray-700">Video URL:</label>
                        <input type="text" id="url" name="url" class="w-full p-2 border border-gray-300 rounded" required>
                    </div>
                    <div>
                        <label for="platform" class="block text-gray-700">Platform:</label>
                        <select id="platform" name="platform" class="w-full p-2 border border-gray-300 rounded">
                            <option value="youtube">YouTube</option>
                            <option value="tiktok">TikTok</option>
                            <option value="instagram">Instagram</option>
                            <option value="facebook">Facebook</option>
                            <option value="twitter">Twitter</option>
                            <option value="dailymotion">Dailymotion</option>
                            <option value="reddit">Reddit</option>
                            <option value="twitch">Twitch</option>
                            <option value="vimeo">Vimeo</option>
                            <option value="snapchat">Snapchat</option>
                        </select>
                    </div>
                    <div>
                        <label for="format" class="block text-gray-700">Format:</label>
                        <select id="format" name="format" class="w-full p-2 border border-gray-300 rounded">
                            <option value="bestvideo+bestaudio/best">Best Video + Best Audio</option>
                            <option value="best">Best</option>
                        </select>
                    </div>
                    <button type="submit" class="w-full bg-blue-500 text-white p-2 rounded">Download</button>
                </form>
                <div id="progress" class="mt-4 hidden">
                    <h2 class="text-xl font-semibold mb-2">Download Progress</h2>
                    <div id="progress-bar" class="w-full bg-gray-200 rounded">
                        <div id="progress-bar-span" class="bg-green-500 text-white text-center p-1 rounded">0%</div>
                    </div>
                    <a id="download-link" href="#" class="mt-2 text-blue-500">Download Completed File</a>
                </div>
            </div>
            <script>
                document.getElementById('download-form').onsubmit = function() {
                    var formData = new FormData(this);
                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', '/download', true);
                    xhr.onload = function() {
                        if (xhr.status === 200) {
                            document.getElementById('progress').classList.remove('hidden');
                        }
                    };
                    xhr.send(formData);
                    return false;
                };

                function updateProgress(percentage) {
                    var progressBarSpan = document.getElementById('progress-bar-span');
                    progressBarSpan.textContent = percentage + '%';
                    progressBarSpan.style.width = percentage + '%';
                }

                var eventSource = new EventSource('/progress');
                eventSource.onmessage = function(event) {
                    updateProgress(event.data);
                };
            </script>
        </body>
        </html>
    ''')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format = request.form['format']
    output_dir = app.config['UPLOAD_FOLDER']
    
    def progress_callback(d):
        if d['status'] == 'downloading':
            percentage = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
            with open('progress.txt', 'w') as f:
                f.write(str(percentage))

    download_thread = threading.Thread(target=download_video, args=(url, format, output_dir, progress_callback))
    download_thread.start()

    return redirect(url_for('index'))

@app.route('/progress')
def progress():
    with open('progress.txt', 'r') as f:
        percentage = f.read().strip()
    return jsonify(percentage)

@app.route('/downloads/latest')
def latest_download():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    if files:
        latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(app.config['UPLOAD_FOLDER'], x)))
        return send_from_directory(app.config['UPLOAD_FOLDER'], latest_file)
    return "No file found."

if __name__ == '__main__':
    app.run(debug=True)
