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

# 英語タイプ名から日本語への変換辞書
TYPE_MAP = {
    "normal": "ノーマル", "fire": "ほのお", "water": "みず", "grass": "くさ",
    "electric": "でんき", "ice": "こおり", "fighting": "かくとう", "poison": "どく",
    "ground": "じめん", "flying": "ひこう", "psychic": "エスパー", "bug": "むし",
    "rock": "いわ", "ghost": "ゴースト", "dragon": "ドラゴン", "dark": "あく",
    "steel": "はがね", "fairy": "フェアリー"
}

# -----------------------------
# API
# -----------------------------
@st.cache_data
def get_pokemon_data(pokemon_id):
    try:
        # 基本データの取得
        data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}").json()

        img_url = data['sprites']['other']['official-artwork']['front_default']
        if not img_url:
            img_url = data['sprites']['front_default']

        # タイプの日本語変換
        types_en = [t['type']['name'] for t in data['types']]
        types_ja = [TYPE_MAP.get(t, t) for t in types_en]

        # 種族データの取得
        s_data = requests.get(data['species']['url']).json()

        # 名前の取得
        name = None
        for lang in ["ja-Hrkt", "ja", "en"]:
            name = next((n['name'] for n in s_data['names'] if n['language']['name'] == lang), None)
            if name:
                break

        # 図鑑説明の取得（ja-Hrkt または ja を優先的に探す）
        desc = ""
        for lang_code in ["ja-Hrkt", "ja"]:
            desc = next((f['flavor_text'] for f in s_data['flavor_text_entries'] if f['language']['name'] == lang_code), "")
            if desc:
                break
        
        # 不要な文字の掃除
        desc = desc.replace('\n', ' ').replace('\f', ' ').replace('\u3000', ' ')

        return name, img_url, types_ja, desc
    except:
        return None, None, None, None

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
    name, img_url, types, desc = get_pokemon_data(pokemon_id)

    st.markdown(f"### 問題 {i+1} / {total}")
    st.markdown(f"正解数: {st.session_state.score} / {total}")

    if img_url:
        st.image(img_url, width=300)

    with st.form(key=f"form_{i}"):
        ans = st.text_input("名前をカタカナで入力", key=f"input_{i}")
        col1, spacer, col2 = st.columns([1, 4, 2])
        submit = col1.form_submit_button("送信")
        stop = col2.form_submit_button("途中終了")

    if submit and st.session_state.result is None:
        # 特殊メッセージ設定
        specials = {
            "ピカチュウ": "10まんボルトだ！",
            "トリトドン": "ぽわ～ぐちょぐちょ",
            "ミカルゲ": "おんみょ～ん",
            "ポッチャマ": "ぽちゃぽっちゃ！",
            "ノココッチ": "にげあしドロー",
            "ヘラクロス": "むし！",
            "ドラパルト": "ファントムダイブ！",
            "サマヨール": "カースドボム！",
            "ヨノワール": "カースドボム！",
            "マシマシラ": "アドレナブレイン！",
            "ゾロアーク": "とりひき！",
            "スボミー": "むずむずかふん！",
            "ビクティニ": "無限のパワー！",
            "ゲッコウガ": "へんげんじざい！",
            "ニャスパー": "もこお！",
            "ミミッキュ": "ラス１なんやかんやできるミミッキュで",
            "パモ": "床の隙間の汚れwatching．かわいいかわいいね"
        }

        if ans == name:
            if name == "ソーナンス":
                msg = "そ～なんす！"
            elif name == "ソーナノ":
                msg = "そ～なの！"
            else:
                extra = specials.get(name, "")
                msg = f"正解！ {extra}".strip()
            
            st.session_state.result = (msg, True)
            st.session_state.score += 1
        else:
            extra = " いぬぬわん！" if (name == "ワンパチ" and ans in ["いぬぬわん", "イヌヌワン"]) else ""
            st.session_state.result = (f"不正解！ 正解は {name}{extra}", False)
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
        
        # タイプと図鑑説明の表示
        if types:
            st.info(f"**タイプ**: {' / '.join(types)}  \n**図鑑説明**: {desc if desc else '図鑑説明が見つかりませんでした。'}")

        # ---- 最終JS（フォーカス削除版）----
        components.html("""
        <script>
        (function() {
            const parentDoc = window.parent.document;
            const isMobile = /iPhone|iPad|iPod|Android|Mobile/i.test(navigator.userAgent);
            if (!isMobile) {
                if (!window.pokemonQuizHandler) {
                    window.pokemonQuizHandler = true;
                    window.lastEnterTime = 0;
                    parentDoc.addEventListener("keydown", function(e) {
                        if (e.key === "Enter") {
                            const bodyText = parentDoc.body.innerText;
                            const hasResult = bodyText.includes("正解") || bodyText.includes("不正解") || bodyText.includes("そ～な");
                            if (!hasResult) return;
                            const now = Date.now();
                            if (now - window.lastEnterTime < 500) return;
                            window.lastEnterTime = now;
                            const buttons = parentDoc.querySelectorAll('button');
                            for (let i = buttons.length - 1; i >= 0; i--) {
                                if (buttons[i].innerText && buttons[i].innerText.includes("次の問題へ")) {
                                    buttons[i].click();
                                    return;
                                }
                            }
                        }
                    });
                }
            }
        })();
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
