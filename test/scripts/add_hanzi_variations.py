import os
import json
import argparse
import re
from typing import List, Dict, Set, Tuple, Any

def get_next_term_bank_number(directory: str) -> int:
    # Find the next available term bank number in the specified directory
    pattern = re.compile(r'term_bank_(\d+)\.json')
    max_number = 0
    
    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            number = int(match.group(1))
            max_number = max(max_number, number)
    
    return max_number + 1

def load_all_term_banks(directory: str) -> Dict[str, List[Any]]:
    # Load all term_bank_*.json files from the specified directory
    term_banks = {}
    pattern = re.compile(r'term_bank_\d+\.json')
    
    for filename in os.listdir(directory):
        if pattern.match(filename):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    term_banks[filename] = json.load(f)
                    print(f"Loaded {filename} with {len(term_banks[filename])} entries")
                except json.JSONDecodeError:
                    print(f"Error: Could not parse {filename} as JSON")
    
    return term_banks

def extract_all_terms(term_banks: Dict[str, List[Any]]) -> Set[str]:
    # Extract all dictionary terms from the term banks
    all_terms = set()
    
    for bank_name, entries in term_banks.items():
        for entry in entries:
            if entry and isinstance(entry, list) and len(entry) > 0 and isinstance(entry[0], str):
                all_terms.add(entry[0])
    
    return all_terms

def create_character_mapping(variant_pairs: List[List[str]]) -> Dict[str, str]:
    # Create a bidirectional mapping of character variants
    mapping = {}
    
    for pair in variant_pairs:
        if len(pair) == 2:
            char1, char2 = pair
            mapping[char1] = char2
            mapping[char2] = char1
    
    return mapping

def generate_term_variants(term: str, char_mapping: Dict[str, str], processed_terms: Set[str] = None) -> List[str]:
    if processed_terms is None:
        processed_terms = set()
    
    processed_terms.add(term)
    
    variants = []
    
    for i, char in enumerate(term):
        if char in char_mapping:
            variant = term[:i] + char_mapping[char] + term[i+1:]
            
            # Only add and process this variant if we haven't seen it before
            if variant not in processed_terms:
                variants.append(variant)
                processed_terms.add(variant)
                
                sub_variants = generate_term_variants(variant, char_mapping, processed_terms)
                variants.extend(sub_variants)
    
    return list(set(variants))

def main(directory: str, variant_pairs: List[List[str]]):
    print(f"Scanning directory: {directory}")
    term_banks = load_all_term_banks(directory)
    if not term_banks:
        print("No term bank files found.")
        return
    
    all_terms = extract_all_terms(term_banks)
    print(f"Found {len(all_terms)} unique terms across all term banks")
    
    char_mapping = create_character_mapping(variant_pairs)
    print(f"Created mapping for {len(char_mapping)} characters")
    
    left_chars = set(pair[0] for pair in variant_pairs)
    print(f"Identified {len(left_chars)} 'left' characters in the mapping")
    
    new_entries = []
    terms_processed = 0
    variants_added = 0
    
    all_entries = []
    for bank_entries in term_banks.values():
        all_entries.extend(bank_entries)
    
    all_processed_terms = set(all_terms)
    
    for entry in all_entries:
        if not entry or not isinstance(entry, list) or len(entry) == 0:
            continue
        
        term = entry[0]
        terms_processed += 1
        
        if not isinstance(term, str):
            continue
        
        variants = generate_term_variants(term, char_mapping, all_processed_terms)
        
        # Add variants that don't already exist
        for variant in variants:
            if variant not in all_terms:
                new_entry = entry.copy()
                new_entry[0] = variant
                
                # Check if this variant contains any "left" characters
                # If so, decrease its search rank by 1
                has_left_char = False
                for i, char in enumerate(variant):
                    if (i < len(term) and char != term[i] and char in left_chars):
                        has_left_char = True
                        break
                
                if has_left_char and len(new_entry) > 4:
                    # Make sure it's a number before decrementing
                    if isinstance(new_entry[4], int):
                        new_entry[4] -= 1
                
                new_entries.append(new_entry)
                all_terms.add(variant)  # Add to set to avoid duplicates
                variants_added += 1
        
        if terms_processed % 1000 == 0:
            print(f"Processed {terms_processed} terms, added {variants_added} variants so far")
    
    # Save new entries to term bank files, with a maximum of 10,000 entries per file
    if new_entries:
        next_number = get_next_term_bank_number(directory)
        
        # Split entries into chunks of 10,000
        entry_chunks = [new_entries[i:i + 10000] for i in range(0, len(new_entries), 10000)]
        
        for i, chunk in enumerate(entry_chunks):
            file_number = next_number + i
            new_file_name = f"term_bank_{file_number}.json"
            new_file_path = os.path.join(directory, new_file_name)
            
            with open(new_file_path, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, ensure_ascii=False)
            
            print(f"Created new term bank file: {new_file_name} with {len(chunk)} entries")
        
        print(f"Total: Created {len(entry_chunks)} new term bank file(s) with {len(new_entries)} entries")
    else:
        print("No new variant entries were generated")


def parse_args():
    parser = argparse.ArgumentParser(description='Process dictionary files for Yomitan conversion')
    parser.add_argument('--input-dir', '-i', type=str, help='Path to the folder containing the PNG images')
    parser.add_argument('--json-file', '-j', type=str, help='Path to the input JSON dictionary file')
    parser.add_argument('--output-file', '-o', type=str, help='Path to the output JSON file')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    dictionary_directory = args.input_dir
    
    kanji_mappings = [
        ['亞', '亜'],
        ['惡', '悪'],
        ['吞', '呑'],
        ['壓', '圧'],
        ['圍', '囲'],
        ['醫', '医'],
        ['爲', '為'],
        ['壹', '壱'],
        ['逸', '逸'],
        ['飮', '飲'],
        ['隱', '隠'],
        ['羽', '羽'],
        ['榮', '栄'],
        ['營', '営'],
        ['銳', '鋭'],
        ['衞', '衛'],
        ['益', '益'],
        ['驛', '駅'],
        ['悅', '悦'],
        ['謁', '謁'],
        ['閱', '閲'],
        ['圓', '円'],
        ['鹽', '塩'],
        ['緣', '縁'],
        ['艷', '艶'],
        ['應', '応'],
        ['歐', '欧'],
        ['毆', '殴'],
        ['櫻', '桜'],
        ['奧', '奥'],
        ['橫', '横'],
        ['溫', '温'],
        ['穩', '穏'],
        ['假', '仮'],
        ['價', '価'],
        ['禍', '禍'],
        ['畫', '画'],
        ['會', '会'],
        ['悔', '悔'],
        ['海', '海'],
        ['繪', '絵'],
        ['壞', '壊'],
        ['懷', '懐'],
        ['慨', '慨'],
        ['槪', '概'],
        ['擴', '拡'],
        ['殼', '殻'],
        ['覺', '覚'],
        ['學', '学'],
        ['嶽', '岳'],
        ['樂', '楽'],
        ['喝', '喝'],
        ['渴', '渇'],
        ['褐', '褐'],
        ['罐', '缶'],
        ['卷', '巻'],
        ['陷', '陥'],
        ['勸', '勧'],
        ['寬', '寛'],
        ['漢', '漢'],
        ['關', '関'],
        ['歡', '歓'],
        ['館', '館'],
        ['觀', '観'],
        ['顏', '顔'],
        ['氣', '気'],
        ['祈', '祈'],
        ['既', '既'],
        ['歸', '帰'],
        ['龜', '亀'],
        ['器', '器'],
        ['僞', '偽'],
        ['戲', '戯'],
        ['犧', '犠'],
        ['舊', '旧'],
        ['據', '拠'],
        ['擧', '挙'],
        ['虛', '虚'],
        ['峽', '峡'],
        ['挾', '挟'],
        ['狹', '狭'],
        ['敎', '教'],
        ['鄕', '郷'],
        ['響', '響'],
        ['曉', '暁'],
        ['勤', '勤'],
        ['謹', '謹'],
        ['區', '区'],
        ['驅', '駆'],
        ['勳', '勲'],
        ['薰', '薫'],
        ['徑', '径'],
        ['莖', '茎'],
        ['契', '契'],
        ['惠', '恵'],
        ['揭', '掲'],
        ['溪', '渓'],
        ['經', '経'],
        ['螢', '蛍'],
        ['輕', '軽'],
        ['繼', '継'],
        ['鷄', '鶏'],
        ['藝', '芸'],
        ['擊', '撃'],
        ['缺', '欠'],
        ['硏', '研'],
        ['縣', '県'],
        ['儉', '倹'],
        ['劍', '剣'],
        ['險', '険'],
        ['圈', '圏'],
        ['檢', '検'],
        ['獻', '献'],
        ['權', '権'],
        ['顯', '顕'],
        ['驗', '験'],
        ['嚴', '厳'],
        ['戶', '戸'],
        ['吳', '呉'],
        ['娛', '娯'],
        ['廣', '広'],
        ['效', '効'],
        ['恆', '恒'],
        ['黃', '黄'],
        ['鑛', '鉱'],
        ['號', '号'],
        ['吿', '告'],
        ['國', '国'],
        ['黑', '黒'],
        ['穀', '穀'],
        ['碎', '砕'],
        ['濟', '済'],
        ['齋', '斎'],
        ['歲', '歳'],
        ['劑', '剤'],
        ['殺', '殺'],
        ['雜', '雑'],
        ['參', '参'],
        ['棧', '桟'],
        ['蠶', '蚕'],
        ['慘', '惨'],
        ['產', '産'],
        ['贊', '賛'],
        ['殘', '残'],
        ['絲', '糸'],
        ['祉', '祉'],
        ['視', '視'],
        ['齒', '歯'],
        ['飼', '飼'],
        ['兒', '児'],
        ['辭', '辞'],
        ['濕', '湿'],
        ['實', '実'],
        ['寫', '写'],
        ['社', '社'],
        ['舍', '舎'],
        ['者', '者'],
        ['煮', '煮'],
        ['釋', '釈'],
        ['壽', '寿'],
        ['收', '収'],
        ['臭', '臭'],
        ['從', '従'],
        ['澁', '渋'],
        ['獸', '獣'],
        ['縱', '縦'],
        ['祝', '祝'],
        ['肅', '粛'],
        ['處', '処'],
        ['暑', '暑'],
        ['署', '署'],
        ['緖', '緒'],
        ['諸', '諸'],
        ['敍', '叙'],
        ['尙', '尚'],
        ['將', '将'],
        ['祥', '祥'],
        ['稱', '称'],
        ['涉', '渉'],
        ['燒', '焼'],
        ['證', '証'],
        ['奬', '奨'],
        ['條', '条'],
        ['狀', '状'],
        ['乘', '乗'],
        ['淨', '浄'],
        ['剩', '剰'],
        ['疊', '畳'],
        ['繩', '縄'],
        ['壤', '壌'],
        ['孃', '嬢'],
        ['讓', '譲'],
        ['釀', '醸'],
        ['觸', '触'],
        ['囑', '嘱'],
        ['神', '神'],
        ['眞', '真'],
        ['寢', '寝'],
        ['愼', '慎'],
        ['盡', '尽'],
        ['圖', '図'],
        ['粹', '粋'],
        ['醉', '酔'],
        ['穗', '穂'],
        ['隨', '随'],
        ['髓', '髄'],
        ['樞', '枢'],
        ['數', '数'],
        ['瀨', '瀬'],
        ['聲', '声'],
        ['靑', '青'],
        ['齊', '斉'],
        ['淸', '清'],
        ['晴', '晴'],
        ['精', '精'],
        ['靜', '静'],
        ['稅', '税'],
        ['竊', '窃'],
        ['攝', '摂'],
        ['節', '節'],
        ['說', '説'],
        ['絕', '絶'],
        ['專', '専'],
        ['淺', '浅'],
        ['戰', '戦'],
        ['踐', '践'],
        ['錢', '銭'],
        ['潛', '潜'],
        ['纖', '繊'],
        ['禪', '禅'],
        ['祖', '祖'],
        ['雙', '双'],
        ['壯', '壮'],
        ['爭', '争'],
        ['莊', '荘'],
        ['搜', '捜'],
        ['插', '挿'],
        ['巢', '巣'],
        ['曾', '曽'],
        ['瘦', '痩'],
        ['裝', '装'],
        ['僧', '僧'],
        ['層', '層'],
        ['總', '総'],
        ['騷', '騒'],
        ['增', '増'],
        ['憎', '憎'],
        ['藏', '蔵'],
        ['贈', '贈'],
        ['臟', '臓'],
        ['卽', '即'],
        ['屬', '属'],
        ['續', '続'],
        ['墮', '堕'],
        ['對', '対'],
        ['體', '体'],
        ['帶', '帯'],
        ['滯', '滞'],
        ['臺', '台'],
        ['瀧', '滝'],
        ['擇', '択'],
        ['澤', '沢'],
        ['脫', '脱'],
        ['擔', '担'],
        ['單', '単'],
        ['膽', '胆'],
        ['嘆', '嘆'],
        ['團', '団'],
        ['斷', '断'],
        ['彈', '弾'],
        ['遲', '遅'],
        ['癡', '痴'],
        ['蟲', '虫'],
        ['晝', '昼'],
        ['鑄', '鋳'],
        ['著', '著'],
        ['廳', '庁'],
        ['徵', '徴'],
        ['聽', '聴'],
        ['懲', '懲'],
        ['敕', '勅'],
        ['鎭', '鎮'],
        ['塚', '塚'],
        ['遞', '逓'],
        ['鐵', '鉄'],
        ['點', '点'],
        ['轉', '転'],
        ['傳', '伝'],
        ['都', '都'],
        ['燈', '灯'],
        ['當', '当'],
        ['黨', '党'],
        ['盜', '盗'],
        ['稻', '稲'],
        ['鬭', '闘'],
        ['德', '徳'],
        ['獨', '独'],
        ['讀', '読'],
        ['突', '突'],
        ['屆', '届'],
        ['內', '内'],
        ['難', '難'],
        ['貳', '弐'],
        ['腦', '悩'],
        ['腦', '脳'],
        ['霸', '覇'],
        ['拜', '拝'],
        ['廢', '廃'],
        ['賣', '売'],
        ['梅', '梅'],
        ['麥', '麦'],
        ['發', '発'],
        ['髮', '髪'],
        ['拔', '抜'],
        ['飯', '飯'],
        ['繁', '繁'],
        ['晚', '晩'],
        ['蠻', '蛮'],
        ['卑', '卑'],
        ['祕', '秘'],
        ['碑', '碑'],
        ['濱', '浜'],
        ['賓', '賓'],
        ['頻', '頻'],
        ['敏', '敏'],
        ['甁', '瓶'],
        ['侮', '侮'],
        ['福', '福'],
        ['拂', '払'],
        ['佛', '仏'],
        ['倂', '併'],
        ['竝', '並'],
        ['塀', '塀'],
        ['餠', '餅'],
        ['邊', '辺'],
        ['變', '変'],
        ['勉', '勉'],
        ['步', '歩'],
        ['舖', '舗'],
        ['寶', '宝'],
        ['豐', '豊'],
        ['襃', '褒'],
        ['墨', '墨'],
        ['沒', '没'],
        ['飜', '翻'],
        ['每', '毎'],
        ['萬', '万'],
        ['滿', '満'],
        ['免', '免'],
        ['麵', '麺'],
        ['默', '黙'],
        ['彌', '弥'],
        ['譯', '訳'],
        ['藥', '薬'],
        ['與', '与'],
        ['豫', '予'],
        ['餘', '余'],
        ['譽', '誉'],
        ['搖', '揺'],
        ['樣', '様'],
        ['謠', '謡'],
        ['來', '来'],
        ['賴', '頼'],
        ['亂', '乱'],
        ['覽', '覧'],
        ['欄', '欄'],
        ['龍', '竜'],
        ['隆', '隆'],
        ['旅', '旅'],
        ['虜', '虜'],
        ['兩', '両'],
        ['獵', '猟'],
        ['綠', '緑'],
        ['淚', '涙'],
        ['壘', '塁'],
        ['類', '類'],
        ['禮', '礼'],
        ['勵', '励'],
        ['戾', '戻'],
        ['靈', '霊'],
        ['隸', '隷'],
        ['齡', '齢'],
        ['曆', '暦'],
        ['歷', '歴'],
        ['戀', '恋'],
        ['連', '連'],
        ['廉', '廉'],
        ['練', '練'],
        ['鍊', '錬'],
        ['爐', '炉'],
        ['勞', '労'],
        ['郞', '郎'],
        ['朗', '朗'],
        ['廊', '廊'],
        ['樓', '楼'],
        ['籠', '篭'],
        ['錄', '録'],
        ['灣', '湾'],

        # 人名用漢字
        ['堯', '尭'],
        ['巖', '巌'],
        ['摑', '掴'],
        ['彥', '彦'],
        ['檜', '桧'],
        ['槇', '槙'],
        ['渚', '渚'],
        ['猪', '猪'],
        ['琢', '琢'],
        ['瑤', '瑶'],
        ['禰', '祢'],
        ['祐', '祐'],
        ['禱', '祷'],
        ['祿', '禄'],
        ['禎', '禎'],
        ['穰', '穣'],
        ['簞', '箪'],
        ['聰', '聡'],
        ['蓮', '蓮'],
        ['蘭', '蘭'],
        ['遙', '遥'],
        ['遼', '遼'],
        ['靖', '靖'],

        # 表外字 (擴張新字體)
        ['蘒', '蘒'],
        ['啞', '唖'],
        ['噓', '嘘'],
        ['穎', '頴'],
        ['鷗', '鴎'],
        ['軀', '躯'],
        ['鶯', '鴬'],
        ['攪', '撹'],
        ['麴', '麹'],
        ['鹼', '鹸'],
        ['嚙', '噛'],
        ['繡', '繍'],
        ['蔣', '蒋'],
        ['醬', '醤'],
        ['搔', '掻'],
        ['屛', '屏'],
        ['幷', '并'],
        ['濾', '沪'],
        ['蘆', '芦'],
        ['蠟', '蝋'],
        ['彎', '弯'],
        ['焰', '焔'],
        ['礦', '砿'],
        ['讚', '讃'],
        ['顚', '顛'],
        ['巓', '巔'],
        ['醱', '醗'],
        ['潑', '溌'],
        ['輛', '輌'],
        ['繫', '繋'],
        ['瀆', '涜'],
        ['儘', '侭'],
        ['藪', '薮'],
        ['蠅', '蝿'],
        ['嬀', '媯'],
        ['驒', '騨'],

        # variants

        # 常用漢字
        ['鬥', '闘'],
        ['鬪', '闘'],
        ['鬬', '闘'],

        # 人名用漢字
        ['亙', '亘'],
        ['凜', '凛'],
        ['晄', '晃'],
        ['晉', '晋'],
        ['萠', '萌'],

        # 新字源 

        ['冬', '冬'],
        ['割', '割'],
        ['勇', '勇'],
        ['周', '周'],
        ['噴', '噴'],
        ['城', '城'],
        ['墳', '墳'],
        ['奔', '奔'],
        ['姬', '姫'],
        ['寧', '寧'],
        ['瓣', '弁'],
        ['辨', '弁'],
        ['辯', '弁'],
        ['彫', '彫'],
        ['惱', '悩'],
        ['慈', '慈'],
        ['憤', '憤'],
        ['憲', '憲'],
        ['成', '成'],
        ['戴', '戴'],
        ['搜', '捜'],
        ['滋', '滋'],
        ['潮', '潮'],
        ['炭', '炭'],
        ['爵', '爵'],
        ['異', '異'],
        ['盛', '盛'],
        ['𥔵', '磁'],
        ['𥳑', '簡'],
        ['糖', '糖'],
        ['𦤶', '致'],
        ['芽', '芽'],
        ['若', '若'],
        ['茶', '茶'],
        ['華', '華'],
        ['落', '落'],
        ['葉', '葉'],
        ['藍', '藍'],
        ['覆', '覆'],
        ['諭', '諭'],
        ['諾', '諾'],
        ['輸', '輸'],
        ['閒', '間'],
        ['降', '降'],

        # 三省堂 
        ['充', '充'],
        ['册', '冊'],
        ['勺', '勺'],
        ['巽', '巽'],
        ['强', '強'],
        ['旣', '既'],
        ['流', '流'],
        ['浩', '浩'],
        ['煕', '熙'],

        # 大修館 
        ['兔', '兎'],
        ['廚', '厨'],
        ['廏', '厩'],
        ['壻', '婿'],
        ['槪', '概']
    ]
    
    hk_variants = [
        ['僞', '偽'],
        ['兌', '兑'],
        ['叄', '叁'],
        ['只', '只衹'],
        ['啓', '啓啟'],
        ['喫', '吃'],
        ['囪', '囱'],
        ['妝', '妝粧'],
        ['媼', '媪'],
        ['嬀', '媯'],
        ['悅', '悦'],
        ['慍', '愠'],
        ['戶', '户'],
        ['挩', '捝'],
        ['搵', '揾'],
        ['擡', '抬'],
        ['敓', '敚'],
        ['敘', '敍敘'],
        ['柺', '枴'],
        ['梲', '棁'],
        ['棱', '稜棱'],
        ['榲', '榅'],
        ['檯', '枱'],
        ['氳', '氲'],
        ['涗', '涚'],
        ['溫', '温'],
        ['溼', '濕'],
        ['潙', '溈'],
        ['潨', '潀'],
        ['熅', '煴'],
        ['爲', '為'],
        ['癡', '痴'],
        ['皁', '皂'],
        ['祕', '秘'],
        ['稅', '税'],
        ['竈', '灶'],
        ['糉', '粽糉糭'],
        ['縕', '緼'],
        ['纔', '才'],
        ['脣', '唇'],
        ['脫', '脱'],
        ['膃', '腽'],
        ['臥', '卧'],
        ['臺', '台'],
        ['菸', '煙'],
        ['蒕', '蒀'],
        ['蔥', '葱'],
        ['蔿', '蒍'],
        ['蘊', '藴'],
        ['蛻', '蜕'],
        ['衆', '眾'],
        ['衛', '衞'],
        ['覈', '核'],
        ['說', '説'],
        ['踊', '踴'],
        ['轀', '輼'],
        ['醞', '醖'],
        ['鉢', '缽'],
        ['鉤', '鈎'],
        ['銳', '鋭'],
        ['鍼', '針'],
        ['閱', '閲'],
        ['鰮', '鰛'],
    ]
    
    jp_shinjitai = [
        ['両', '兩輛'],
        ['弁', '辨辯瓣辦弁'],
        ['御', '御禦'],
        ['欠', '缺欠'],
        ['浜', '濱浜'],
        ['糸', '絲糸'],
        ['芸', '藝芸'],
    ]
    
    jp_shinjitai_phrases = [
        ['一獲千金','一攫千金'],
        ['丁寧','叮嚀'],
        ['丁重','鄭重'],
        ['三差路','三叉路'],
        ['世論','輿論'],
        ['亜鈴','啞鈴'],
        ['交差','交叉'],
        ['供宴','饗宴'],
        ['俊馬','駿馬'],
        ['保塁','堡壘'],
        ['個条書','箇条書'],
        ['偏平','扁平'],
        ['停泊','碇泊'],
        ['優俊','優駿'],
        ['先兵','尖兵'],
        ['先鋭','尖鋭'],
        ['共役','共軛'],
        ['冗舌','饒舌'],
        ['凶器','兇器'],
        ['削岩','鑿岩'],
        ['包丁','庖丁'],
        ['包帯','繃帯'],
        ['区画','區劃'],
        ['厳然','儼然'],
        ['友宜','友誼'],
        ['反乱','叛乱'],
        ['収集','蒐集'],
        ['叙情','抒情'],
        ['台頭','擡頭'],
        ['合弁','合辦'],
        ['喜遊曲','嬉遊曲'],
        ['嘆願','歎願'],
        ['回転','廻転'],
        ['回遊','回游'],
        ['奉持','捧持'],
        ['委縮','萎縮'],
        ['展転','輾轉'],
        ['希少','稀少'],
        ['幻惑','眩惑'],
        ['広範','廣汎'],
        ['広野','曠野'],
        ['廃虚','廢墟'],
        ['建坪率','建蔽率'],
        ['弁当','辨當'],
        ['弁膜','瓣膜'],
        ['弁護','辯護'],
        ['弁髪','辮髮'],
        ['弦歌','絃歌'],
        ['恩義','恩誼'],
        ['意向','意嚮'],
        ['慰謝料','慰藉料'],
        ['憶断','臆断'],
        ['憶病','臆病'],
        ['戦没','戰歿'],
        ['扇情','煽情'],
        ['手帳','手帖'],
        ['技量','伎倆'],
        ['抜粋','抜萃'],
        ['披歴','披瀝'],
        ['抵触','牴触'],
        ['抽選','抽籤'],
        ['拘引','勾引'],
        ['拠出','醵出'],
        ['拠金','醵金'],
        ['掘削','掘鑿'],
        ['控除','扣除'],
        ['援護','掩護'],
        ['放棄','抛棄'],
        ['散水','撒水'],
        ['敬謙','敬虔'],
        ['敷延','敷衍'],
        ['断固','断乎'],
        ['族生','簇生'],
        ['昇叙','陞敘'],
        ['暖房','煖房'],
        ['暗唱','暗誦'],
        ['暗夜','闇夜'],
        ['暴露','曝露'],
        ['枯渇','涸渇'],
        ['格好','恰好'],
        ['格幅','恰幅'],
        ['棄損','毀損'],
        ['模索','摸索'],
        ['橋頭保','橋頭堡'],
        ['欠缺','欠缺'],
        ['死体','屍體'],
        ['殿部','臀部'],
        ['母指','拇指'],
        ['気迫','気魄'],
        ['決別','訣別'],
        ['決壊','決潰'],
        ['沈殿','沈澱'],
        ['油送船','油槽船'],
        ['波乱','波瀾'],
        ['注釈','註釋'],
        ['洗浄','洗滌|洗浄'],
        ['活発','活潑'],
        ['浸透','滲透'],
        ['浸食','浸蝕'],
        ['消却','銷卻'],
        ['混然','渾然'],
        ['湾曲','彎曲'],
        ['溶接','熔接'],
        ['漁労','漁撈'],
        ['漂然','飄然'],
        ['激高','激昂'],
        ['火炎','火焰'],
        ['焦燥','焦躁'],
        ['班点','斑点'],
        ['留飲','溜飲'],
        ['略奪','掠奪'],
        ['疎通','疏通'],
        ['発酵','醱酵'],
        ['白亜','白堊'],
        ['相克','相剋'],
        ['知恵','智慧'],
        ['破棄','破毀'],
        ['確固','確乎'],
        ['禁固','禁錮'],
        ['符丁','符牒'],
        ['粉装','扮装'],
        ['紫班','紫斑'],
        ['終息','終熄'],
        ['総合','綜合'],
        ['編集','編輯'],
        ['義援','義捐'],
        ['耕運機','耕耘機'],
        ['肝心','肝腎'],
        ['肩甲骨','肩胛骨'],
        ['背徳','悖德'],
        ['脈拍','脈搏'],
        ['膨張','膨脹'],
        ['芳純','芳醇'],
        ['英知','叡智'],
        ['蒸留','蒸溜'],
        ['薫蒸','燻蒸'],
        ['薫製','燻製'],
        ['衣装','衣裳'],
        ['衰退','衰退|衰頽'],
        ['裕然','悠然'],
        ['補佐','輔佐'],
        ['訓戒','訓誡'],
        ['試練','試煉'],
        ['詭弁','詭辯'],
        ['講和','媾和'],
        ['象眼','象嵌'],
        ['貫録','貫禄'],
        ['買弁','買辦'],
        ['賛辞','讚辭'],
        ['踏襲','蹈襲'],
        ['車両','車輛'],
        ['転倒','顛倒'],
        ['輪郭','輪廓'],
        ['退色','褪色'],
        ['途絶','杜絶'],
        ['連係','連繫'],
        ['連合','聯合'],
        ['選考','銓衡'],
        ['酢酸','醋酸'],
        ['野卑','野鄙'],
        ['鉱石','礦石'],
        ['間欠','間歇'],
        ['関数','函數'],
        ['防御','防禦'],
        ['険阻','嶮岨'],
        ['障壁','牆壁'],
        ['障害','障礙'],
        ['隠滅','湮滅'],
        ['集落','聚落'],
        ['雇用','雇傭'],
        ['風諭','諷喩'],
        ['飛語','蜚語'],
        ['香典','香奠'],
        ['骨格','骨骼'],
        ['高進','亢進'],
        ['鳥観','鳥瞰'],
    ]
    
    
    main(dictionary_directory, kanji_mappings)