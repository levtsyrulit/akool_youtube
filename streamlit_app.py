import streamlit as st
import psycopg2
import re


# Function to extract video ID from YouTube URL
def extract_video_id(url):
    regex = r"(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$"
    if re.match(regex, url):
        video_id = url.split("v=")[-1].split("&")[0]
        return video_id
    return None


# Function to check if video ID exists in the database
def check_video_id_exists(conn, video_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM youtube_videos WHERE video_id = %s", (video_id,))
        return cur.fetchone() is not None


# Function to add video ID to the database
def add_video_id(conn, video_id):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO youtube_videos (video_id) VALUES (%s)", (video_id,))
        conn.commit()


# Streamlit app
def main():
    st.title("YouTube Video Checker")

    # Database connection
    conn = psycopg2.connect(
        host="ep-calm-star-76049617.us-west-2.retooldb.com",
        database="retool",
        user="retool",
        password="hed3ZnNfxy6B"
    )

    # Input for YouTube URL
    youtube_url = st.text_input("Enter YouTube URL:")

    if youtube_url:
        video_id = extract_video_id(youtube_url)
        if video_id:
            if check_video_id_exists(conn, video_id):
                st.warning("This video has already been added.")
            else:
                add_video_id(conn, video_id)
                st.success("Video has been sent.")
        else:
            st.error("Invalid YouTube URL.")

    conn.close()


if __name__ == "__main__":
    main()
