import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import cv2
import tempfile
import os
import json

st.set_page_config(page_title="Unified Annotation Tool", layout="wide")
st.title("🧠 Unified Annotation Tool (Text, Image, Audio, Video)")

tab1, tab2, tab3, tab4 = st.tabs(["📝 Text", "🖼️ Image", "🎧 Audio", "🎥 Video"])

# -------------------------------
# 📝 TEXT ANNOTATION
# -------------------------------
with tab1:
    st.header("📝 Text Annotation")

    sample_texts = st.text_area("Paste multiple texts (one per line):", height=150)

    if sample_texts:
        lines = [line.strip() for line in sample_texts.strip().split("\n") if line.strip()]
        labels = []
        st.write("### Annotate Each Line")

        for i, text in enumerate(lines):
            st.markdown(f"**{i+1}.** {text}")
            label = st.selectbox(
                f"Label for line {i+1}",
                options=["Positive", "Neutral", "Negative", "Other"],
                key=f"text_label_{i}"
            )
            labels.append({"text": text, "label": label})

        if labels:
            st.subheader("🧾 Annotations")
            st.json(labels)

            text_json = json.dumps({"annotations": labels}, indent=2)
            st.download_button("📥 Download JSON", text_json, file_name="text_annotations.json", mime="application/json")


# -------------------------------
# 🖼️ IMAGE ANNOTATION
# -------------------------------
with tab2:
    st.header("🖼️ Image Annotation")

    uploaded_img = st.file_uploader("Upload an image (JPG/PNG)", type=["png", "jpg", "jpeg"], key="img_uploader")

    if uploaded_img:
        image = Image.open(uploaded_img)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        canvas_result = st_canvas(
            fill_color="",
            stroke_width=2,
            stroke_color="#FF0000",
            background_image=image,
            update_streamlit=True,
            height=image.height,
            width=image.width,
            drawing_mode="rect",
            key="canvas_image",
        )

        labels = []
        if canvas_result.json_data:
            for i, obj in enumerate(canvas_result.json_data["objects"]):
                if obj["type"] == "rect":
                    left = obj["left"]
                    top = obj["top"]
                    width = obj["width"]
                    height = obj["height"]
                    bbox = [int(left), int(top), int(left + width), int(top + height)]
                    label = st.text_input(f"Label for box {i+1} (at {bbox})", key=f"label_img_{i}")
                    if label:
                        labels.append({"label": label, "bbox": bbox})

        if labels:
            st.subheader("📦 Image Annotations")
            st.json(labels)

            img_json = json.dumps({
                "image_file": uploaded_img.name,
                "annotations": labels
            }, indent=2)

            st.download_button("📥 Download JSON", img_json, file_name="image_annotations.json", mime="application/json")


# -------------------------------
# 🎧 AUDIO ANNOTATION
# -------------------------------
with tab3:
    st.header("🎧 Audio Annotation")

    uploaded_audio = st.file_uploader("Upload audio file (MP3/WAV/OGG)", type=["mp3", "wav", "ogg"], key="audio_uploader")

    if uploaded_audio:
        st.audio(uploaded_audio, format='audio/mp3')

        transcript = st.text_area("📝 Transcript", placeholder="Type what you hear...")
        label = st.selectbox("🔖 Label", options=["Speech", "Music", "Noise", "Silence"])

        if st.button("💾 Save Audio Annotation", key="save_audio"):
            audio_annotation = {
                "file": uploaded_audio.name,
                "transcript": transcript,
                "label": label
            }

            st.success("Annotation saved ⬇️")
            st.json(audio_annotation)

            audio_json = json.dumps(audio_annotation, indent=2)
            st.download_button("📥 Download JSON", audio_json, file_name=f"{uploaded_audio.name}_annotation.json", mime="application/json")


# -------------------------------
# 🎥 VIDEO ANNOTATION
# -------------------------------
with tab4:
    st.header("🎥 Video Frame Annotation")

    uploaded_video = st.file_uploader("Upload a video (MP4/AVI)", type=["mp4", "avi", "mov"])

    if uploaded_video:
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_video.read())

        cap = cv2.VideoCapture(tfile.name)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        st.write(f"Total Frames: {total_frames}, FPS: {fps:.2f}")

        extract_every_n_frames = st.slider("Extract every Nth frame", min_value=1, max_value=100, value=30)
        frame_number = st.slider("Select frame to annotate", 0, total_frames - 1, step=extract_every_n_frames)

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, frame = cap.read()

        if success:
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img)
            st.image(pil_img, caption=f"Frame {frame_number}", use_column_width=True)

            canvas_result = st_canvas(
                fill_color="",
                stroke_width=2,
                stroke_color="#00FF00",
                background_image=pil_img,
                update_streamlit=True,
                height=pil_img.height,
                width=pil_img.width,
                drawing_mode="rect",
                key=f"canvas_video_{frame_number}",
            )

            video_labels = []
            if canvas_result.json_data:
                for i, obj in enumerate(canvas_result.json_data["objects"]):
                    if obj["type"] == "rect":
                        left = obj["left"]
                        top = obj["top"]
                        width = obj["width"]
                        height = obj["height"]
                        bbox = [int(left), int(top), int(left + width), int(top + height)]
                        label = st.text_input(f"Label for Box {i+1} (at {bbox})", key=f"label_vid_{frame_number}_{i}")
                        if label:
                            video_labels.append({"frame": frame_number, "label": label, "bbox": bbox})

            if video_labels:
                st.subheader("🎞️ Video Annotations")
                st.json(video_labels)

                video_json = json.dumps({
                    "video_file": uploaded_video.name,
                    "annotations": video_labels
                }, indent=2)

                st.download_button("📥 Download JSON", video_json, file_name=f"frame_{frame_number}_annotations.json", mime="application/json")

        cap.release()
        os.unlink(tfile.name)
