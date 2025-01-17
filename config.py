YDL_OPTS = {
                'format': 'wav/bestaudio/best',
                # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
                'postprocessors': [{  # Extract audio using ffmpeg
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
                'outtmpl': './resources/tmp/%(id)s.%(ext)s',
            }
OUTPUT_DIR='./resources/tmp'