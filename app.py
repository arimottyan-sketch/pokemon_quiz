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
        data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}").json()
        img_url = data['sprites']['other']['official-artwork']['front_default'] or data['sprites']['front_default']
        types_ja = [TYPE_MAP.get(t['type']['name'], t['type']['name']) for t in data['types']]
        s_data = requests.get(data['species']['url']).json()
        name = None
        for lang in ["ja-Hrkt", "ja", "en"]:
            name = next((n['name'] for n in s_data['names'] if n['language']['name'] == lang), None)
            if name: break
        desc = ""
        for lang_code in ["ja-Hrkt", "ja"]:
            desc = next((f['flavor_text'] for f in s_data['flavor_text_entries'] if f['language']['name'] == lang_code), "")
            if desc: break
        desc = desc.replace('\n', ' ').replace('\f', ' ').replace('\u3000', ' ')
        return name, img_url, types_ja, desc
    except:
        return None, None, None, None

# -----------------------------
# 初期化
# -----------------------------
def init_game(ids, is_review=False):
    st.session_state.ids = ids
    random.shuffle(st.session_state.ids)
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.finished = False
    st.session_state.result = None
    if not is_review:
        st.session_state.missed = []

# -----------------------------
# UI
# -----------------------------
st.title("ポケモンクイズ")

if "ids" not in st.session_state:
    region = st.selectbox("地方を選択", list(REGIONS.keys()))
    if st.button("開始"):
        init_game(list(REGIONS[region]))
        st.rerun()

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
        specials = {
            "ピカチュウ": "10まんボルトだ！", "トリトドン": "ぽわ～ぐちょぐちょ", "ミカルゲ": "おんみょ～ん",
            "ポッチャマ": "ぽちゃぽっちゃ！", "ノココッチ": "にげあしドロー", "ヘラクロス": "むし！",
            "ドラパルト": "ファントムダイブ！", "サマヨール": "カースドボム！", "ヨノワール": "カースドボム！",
            "マシマシラ": "アドレナブレイン！", "ゾロアーク": "とりひき！", "スボミー": "むずむずかふん！",
            "ビクティニ": "無限のパワー！", "ゲッコウガ": "へんげんじざい！", "ニャスパー": "もこお！",
            "ミミッキュ": "ラス１なんやかんやできるミミッキュで", "パモ": "床の隙間の汚れwatching．かわいいかわいいね"
        }

        if ans == name:
            if name == "ソーナンス": msg = "そ～なんす！"
            elif name == "ソーナノ": msg = "そ～なの！"
            else: msg = f"正解！ {specials.get(name, '')}".strip()
            
            st.session_state.result = (msg, True)
            st.session_state.score += 1
            # 復習中ならミスリストから削除
            if pokemon_id in st.session_state.missed:
                st.session_state.missed.remove(pokemon_id)
        else:
            extra = " いぬぬわん！" if (name == "ワンパチ" and ans in ["いぬぬわん", "イヌヌワン"]) else ""
            st.session_state.result = (f"不正解！ 正解は {name}{extra}", False)
            # 初めてミスした時だけ追加
            if pokemon_id not in st.session_state.missed:
                st.session_state.missed.append(pokemon_id)

    if stop:
        # 途中終了時、未回答の問題をミスリストに追加（復習時に再度出るようにする）
        remaining_ids = ids[i:]
        if st.session_state.result and st.session_state.result[1] == False:
            # 今解いて不正解だったものは既にmissedに入っている。未回答分はi+1以降
            remaining_ids = ids[i+1:]
        elif st.session_state.result and st.session_state.result[1] == True:
            # 正解した場合はi+1以降
            remaining_ids = ids[i+1:]
            
        for rid in remaining_ids:
            if rid not in st.session_state.missed:
                st.session_state.missed.append(rid)
        
        st.session_state.finished = True
        st.rerun()

    if st.session_state.result:
        message, is_correct = st.session_state.result
        if is_correct: st.success(message)
        else: st.error(message)
        if types: st.info(f"**タイプ**: {' / '.join(types)}  \n**図鑑説明**: {desc or '図鑑説明が見つかりませんでした。'}")

        components.html("""
        <script>
        (function() {
            const parentDoc = window.parent.document;
            if (!/iPhone|iPad|iPod|Android|Mobile/i.test(navigator.userAgent)) {
                if (!window.pokemonQuizHandler) {
                    window.pokemonQuizHandler = true;
                    window.lastEnterTime = 0;
                    parentDoc.addEventListener("keydown", function(e) {
                        if (e.key === "Enter") {
                            const bodyText = parentDoc.body.innerText;
                            if (!(bodyText.includes("正解") || bodyText.includes("不正解") || bodyText.includes("そ～な"))) return;
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

if "finished" in st.session_state and st.session_state.finished:
    st.header("終了")
    st.write(f"スコア: {st.session_state.score} / {len(st.session_state.ids)}")
    
    if st.session_state.missed:
        st.write(f"現在のミス保持数: {len(st.session_state.missed)}問")
        if st.button("ミスだけ復習"):
            # 復習モードとして初期化
            init_game(st.session_state.missed.copy(), is_review=True)
            st.rerun()
    else:
        st.success("全問正解！")

    if st.button("最初に戻る"):
        st.session_state.clear()
        st.rerun()
