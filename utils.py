import re

def get_video_id(youtube_url):
    '''
    Get video id from youtube url
    :param youtube_url: str, youtube url
    :return: str, video id
    '''
    return re.findall(r"v=([a-zA-Z0-9_-]+)", youtube_url)[0]
    # return youtube_url.split('=')[-1]

    
