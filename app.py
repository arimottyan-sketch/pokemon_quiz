import streamlit as st
import requests
import random
import streamlit.components.v1 as components

# -----------------------------
# 設定
# -----------------------------
REGIONS = {
    "カントー (1-151)": range(1, 152),
    "ジョウト (152-251)": range(152, 252),
    "ホウエン (252-386)": range(252, 387),
    "シンオウ (387-493)": range(387, 494),
    "イッシュ (494-649)": range(494, 650),
    "カロス (650-721)": range(650, 722),
    "アローラ (722-809)": range(722, 810),
    "ガラル (810-898)": range(810, 899),
    "パルデア (899-1025)": range(899, 1026)
}

# -----------------------------
# API
# -----------------------------
@st.cache_data
def get_pokemon_data(pokemon_id):
    try:
        data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}").json()

        img_url = data['sprites']['other']['official-artwork']['front_default']
        if not img_url:
            img_url = data['sprites']['front_default']

        s_data = requests.get(data['species']['url']).json()

        name = None
        for lang in ["ja-Hrkt", "ja", "en"]:
            name = next((n['name'] for n in s_data['names'] if n['language']['name'] == lang), None)
            if name:
                break

        return name, img_url
    except:
        return None, None

# -----------------------------
# 初期化
# -----------------------------
def init_game(ids):
    st.session_state.ids = ids
    random.shuffle(st.session_state.ids)
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.missed = []
    st.session_state.finished = False
    st.session_state.result = None

# -----------------------------
# UI
# -----------------------------
st.title("ポケモンクイズ")

# 地方選択
if "ids" not in st.session_state:
    region = st.selectbox("地方を選択", list(REGIONS.keys()))
    if st.button("開始"):
        init_game(list(REGIONS[region]))
        st.rerun()

# ゲーム本体
if "ids" in st.session_state and not st.session_state.finished:
    ids = st.session_state.ids
    i = st.session_state.index
    total = len(ids)

    if i >= total:
        st.session_state.finished = True
        st.rerun()

    pokemon_id = ids[i]
    name, img_url = get_pokemon_data(pokemon_id)

    st.markdown(f"### 問題 {i+1} / {total}")
    st.markdown(f"正解数: {st.session_state.score} / {total}")

    if img_url:
        st.image(img_url, width=300)

    with st.form(key=f"form_{i}"):
        ans = st.text_input("名前をカタカナで入力", key=f"input_{i}")
        col1, spacer, col2 = st.columns([1, 4, 2])
        submit = col1.form_submit_button("送信")
        stop = col2.form_submit_button("途中終了")

    if submit:
        if ans == name:
            st.session_state.result = ("正解！", True)
            st.session_state.score += 1
        else:
            st.session_state.result = (f"不正解！ 正解は {name}", False)
            st.session_state.missed.append(pokemon_id)

    if stop:
        st.session_state.finished = True
        st.rerun()

    # 結果表示
    if st.session_state.result:
        message, is_correct = st.session_state.result
        if is_correct:
            st.success(message)
        else:
            st.error(message)

        # ---- JS（ここだけ強化）----
        components.html("""
        <script>
        if (!window.enterHandlerAdded) {
            window.enterHandlerAdded = true;
            window.lastEnterTime = 0;

            document.addEventListener("keydown", function(e) {

                const isMobile = /iPhone|Android.+Mobile/.test(navigator.userAgent);

                if (e.key === "Enter") {

                    if (isMobile) return; // スマホは無視

                    const now = Date.now();

                    // 送信直後は無効（0.5秒）
                    if (now - window.lastEnterTime < 500) return;

                    window.lastEnterTime = now;

                    const buttons = window.parent.document.querySelectorAll('button');

                    buttons.forEach(btn => {
                        if (btn.innerText.includes("次の問題へ")) {
                            btn.click();
                        }
                    });
                }
            });
        }

        // フォーカス
        setTimeout(() => {
            const inputs = window.parent.document.querySelectorAll('input');
            if (inputs.length > 0) {
                inputs[inputs.length - 1].focus();
            }
        }, 200);
        </script>
        """, height=0)

        if st.button("次の問題へ"):
            st.session_state.index += 1
            st.session_state.result = None
            st.rerun()

# 終了画面
if "finished" in st.session_state and st.session_state.finished:
    total = len(st.session_state.ids)
    answered = st.session_state.index

    st.header("終了")
    st.write(f"スコア: {st.session_state.score} / {total}")
    st.write(f"解答数: {answered} / {total}")

    if st.session_state.missed:
        st.write(f"ミス問題数: {len(st.session_state.missed)}")

        if st.button("ミスだけ復習"):
            init_game(st.session_state.missed.copy())
            st.rerun()
    else:
        st.success("全問正解！")

    if st.button("最初に戻る"):
        st.session_state.clear()
        st.rerun()
