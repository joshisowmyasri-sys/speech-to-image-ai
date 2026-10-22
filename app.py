
import time
import requests
import streamlit as st
from streamlit_mic_recorder import speech_to_text

# ---------------------------------
# APP SETTINGS
# ---------------------------------

st.set_page_config(
    page_title="Fairy Tale Speech to Image AI",
    page_icon="🧚",
    layout="centered"
)

API_URL = "https://aihorde.net/api/v2"

HEADERS = {
    "apikey": "0000000000",
    "Client-Agent": "FairyTaleSpeechToImage:1.0"
}

st.title("🧚 Fairy-Tale Speech to Image AI")
st.write(
    "Speak your imagination, edit your words, "
    "and turn them into a storybook illustration!"
)

# ---------------------------------
# SAVE APP STATE
# ---------------------------------

if "prompt" not in st.session_state:
    st.session_state.prompt = ""

if "generated_image" not in st.session_state:
    st.session_state.generated_image = None

# ---------------------------------
# MICROPHONE
# ---------------------------------

st.subheader("🎤 Step 1: Speak your idea")

spoken_text = speech_to_text(
    language="en",
    start_prompt="🎤 Start Speaking",
    stop_prompt="⏹️ Stop Speaking",
    just_once=True,
    use_container_width=True,
    key="storybook_mic"
)

if spoken_text and spoken_text.strip():
    st.session_state.prompt = spoken_text.strip()

# ---------------------------------
# EDITABLE TEXT BOX
# ---------------------------------

st.subheader("✍️ Step 2: Check your words")

prompt = st.text_area(
    "Your spoken description",
    key="prompt",
    height=120,
    placeholder=(
        "Example: A little girl walking through "
        "an enchanted forest with glowing butterflies."
    )
)

st.caption(
    "Check the recognized words and correct them before generating."
)

# ---------------------------------
# IMAGE GENERATION
# ---------------------------------

st.subheader("🎨 Step 3: Create your illustration")

if st.button("✨ Generate Storybook Image", use_container_width=True):

    if not prompt.strip():
        st.warning("Please speak an idea or enter some words first.")

    else:
        st.session_state.generated_image = None

        positive_prompt = (
            "Beautiful fairy-tale storybook illustration, "
            "highly detailed magical fantasy artwork, "
            "professional children's picture-book art, "
            "delicate hand-painted textures, rich harmonious colors, "
            "soft magical lighting, beautiful composition, "
            "expressive characters, detailed background, "
            "tiny sparkling lights, dreamy enchanted atmosphere. "
            "Create an illustration based on this exact scene: "
            + prompt.strip()
        )

        negative_prompt = (
            "blurry, low quality, low resolution, pixelated, "
            "poorly drawn, distorted faces, malformed hands, "
            "extra fingers, extra limbs, duplicated characters, "
            "unfinished artwork, text, watermark, logo, "
            "photograph, photorealistic, realistic camera image"
        )

        payload = {
            "prompt": positive_prompt + "###" + negative_prompt,
            "params": {
                "width": 512,
                "height": 512,
                "steps": 30,
                "n": 1,
                "cfg_scale": 7.5,
                "karras": True,
                "censor_nsfw": True
            },
            "nsfw": False,
            "censor_nsfw": True,
            "r2": True,
            "shared": False
        }

        try:
            with st.spinner(
                "🪄 Sending your idea to the free AI service..."
            ):
                response = requests.post(
                    f"{API_URL}/generate/async",
                    headers=HEADERS,
                    json=payload,
                    timeout=60
                )

                if response.status_code != 202:
                    st.error(
                        "The AI service did not accept the request. "
                        f"HTTP status: {response.status_code}"
                    )
                    st.code(response.text[:1000])
                    st.stop()

                request_id = response.json().get("id")

                if not request_id:
                    st.error("The AI service did not return a request ID.")
                    st.stop()

            progress = st.progress(0)
            status_message = st.empty()
            image_url = None
            start_time = time.time()
            timeout_seconds = 600

            while time.time() - start_time < timeout_seconds:
                check_response = requests.get(
                    f"{API_URL}/generate/check/{request_id}",
                    headers=HEADERS,
                    timeout=30
                )
                check_response.raise_for_status()
                check_data = check_response.json()

                if check_data.get("faulted"):
                    st.error(
                        "The AI generation failed. Please try again "
                        "with a simpler description."
                    )
                    st.stop()

                if check_data.get("done"):
                    break

                wait_time = check_data.get("wait_time", 10)
                elapsed = time.time() - start_time
                progress.progress(min(int(elapsed / timeout_seconds * 100), 95))
                status_message.info(
                    "🎨 Creating your illustration... "
                    "Free community workers may take a while."
                )
                time.sleep(min(max(wait_time, 5), 15))

            else:
                st.warning(
                    "This request is taking too long. Please try again later."
                )
                st.stop()

            with st.spinner("🌟 Finishing your image..."):
                result_response = requests.get(
                    f"{API_URL}/generate/status/{request_id}",
                    headers=HEADERS,
                    timeout=60
                )
                result_response.raise_for_status()
                result_data = result_response.json()

            generations = result_data.get("generations", [])

            if not generations:
                st.error(
                    "The service finished without returning an image. "
                    "Please try again later."
                )
                st.stop()

            image_url = generations[0].get("img")

            if not image_url:
                st.error("No image link was returned by the service.")
                st.stop()

            with st.spinner("🖼️ Loading your storybook image..."):
                image_response = requests.get(
                    image_url,
                    timeout=90
                )
                image_response.raise_for_status()

                st.session_state.generated_image = image_response.content

            progress.progress(100)
            status_message.success("Your illustration is ready! ✨")

        except requests.exceptions.Timeout:
            st.error(
                "The request timed out. The free service may be busy. "
                "Please try again."
            )

        except requests.exceptions.RequestException as error:
            st.error(f"Connection problem: {error}")

        except Exception as error:
            st.error(f"Something went wrong: {error}")

# ---------------------------------
# DISPLAY IMAGE
# ---------------------------------

if st.session_state.generated_image:
    st.subheader("📖 Your Fairy-Tale Illustration")

    st.image(
        st.session_state.generated_image,
        caption="Your AI-generated storybook illustration",
        use_container_width=True
    )

    st.success("Your story has become an illustration! 🧚")
