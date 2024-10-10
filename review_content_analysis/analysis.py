# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import re
import time
import json
import matplotlib.pyplot as plt
from openai import OpenAI
import multiprocessing

FONT_SIZE = 20

COLORS = ['#26547c', '#06d6a0', '#ef476f', '#ffd166']

openai_api_key = os.getenv("OPENAI_KEY")
# print(openai.api_key)

base_dir = '/home/v-qinlinzhao/agent4reviews/simulated_review/reviews'
save_base_dir = '/home/v-qinlinzhao/agent4reviews/simulated_review/classified_reason/'

with open('iter_prompt.txt', 'r') as f:
    iter_prompt = f.read()
    
with open('classification_prompt.txt', 'r') as f:
    classification_prompt = f.read()

with open('reason_library.txt', 'r') as f:
    reason_library = f.read()

def get_gpt_response(prompt):
    client = OpenAI(api_key=openai_api_key)
    messages = [{'role': 'user', 'content': prompt}]
    completion = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )

    response = completion.choices[0].message.content
    response = response.strip()
    
    # time.sleep(5)
    return response

def extract_review_from_real_data():
    base_dir = '/home/v-qinlinzhao/agent4reviews/real_review/original_data'
    result_dir = '/home/v-qinlinzhao/agent4reviews/real_review/extracted_real_review/'
    # 目录为 ICLR202X/notes/xxx.json
    # 将其中所有的json文件的review提取处理
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json'):
                with open(os.path.join(root, file), 'r') as f:
                    data = json.load(f)
                    reviews = []
                    data = data['details']['replies']
                    id = []
                    for d in data:
                        if d['id'] not in id:
                            id.append(d['id'])
                            # 2020-2021
                            if 'content' in d and 'review' in d['content']:
                                reviews.append(d['content']['review'])
                            # 2022
                            if 'content' in d and 'main_review' in d['content']:
                                reviews.append(d['content']['main_review'])
                            # 2023
                            if 'content' in d and 'strength_and_weaknesses' in d['content']:
                                reviews.append(d['content']['strength_and_weaknesses'])
                                
                    # 将每个review分别存入到json文件中，命名格式为 {当前文件名}_{序号}.json
                    # 同时保持每个文件在原目录下相对路径    
                    relative_dir = os.path.relpath(root, base_dir)
                    result_file_dir = os.path.join(result_dir, relative_dir)
                    os.makedirs(result_file_dir, exist_ok=True) 
                       
                    file_base_name = os.path.splitext(file)[0]
                    
                    for i, review in enumerate(reviews): 
                        result_file_name = f"{file_base_name}_{i}.json"
                        result_file_path = os.path.join(result_file_dir, result_file_name)
                        
                        with open(result_file_path, 'w') as result_file:
                            json.dump({"review": review}, result_file, ensure_ascii=False, indent=4)

def extract_meta_review_from_simulated_data():
    base_dir = '/home/v-qinlinzhao/agent4reviews/simulated_review/full_paper_discussion'
    result_dir = '/home/v-qinlinzhao/agent4reviews/simulated_review/meta_review/'
    # 目录为 ICLR202X/notes/xxx.json
    # 将其中所有的json文件的review提取处理
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json'):
                with open(os.path.join(root, file), 'r') as f:
                    data = json.load(f)
                    # review在data['messages']中最后一个元素中的"content"中
                    review = data['messages'][-1]['content']
                # write review into file, keep the abstract path 
                relative_dir = os.path.relpath(root, base_dir)
                result_file_dir = os.path.join(result_dir, relative_dir)
                os.makedirs(result_file_dir, exist_ok=True)
                result_file_path = os.path.join(result_file_dir, file)
                with open(result_file_path, 'w') as result_file:
                    json.dump({"meta_review": review}, result_file, ensure_ascii=False, indent=4)
                    
# Select 1% of the data randomly, let GPT-4 summarize the reasons, and add them to the reason library if there are reasons that do not exist
def construct_reason_library():
    
    base_dir = '/home/v-qinlinzhao/agent4reviews/paper_review_and_rebuttal/selected_files/'
    
    json_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))

    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            review = data['review']
            prompt = iter_prompt.format(review=review, 
                                        reason_library=reason_library)
            ans = get_gpt_response(prompt)
            print(ans)

def analyze_reason_in_batch(json_files):
    
    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)
            review = data['review']
            prompt = classification_prompt.format(review=review)
            res = get_gpt_response(prompt)
            
            # 解析res的输出，将accept和reject的原因分别提取出来，写成json格式
            # 依据该字符串分别抽取Accept和Reject的原因
            reason_dict = {}
            if 'Reject' in res:
                accept_reason = re.search(r"Accept: (.+?);", res)
            else:
                accept_reason = re.search(r"Accept: (.+)", res)
                
            reject_reason = re.search(r"Reject: (.+)", res)
            # print(reject_reason)
            if accept_reason:
                accept_reason = accept_reason.group(1).split(',')
                reason_dict['accept'] = []
                for r in accept_reason:
                    r = r.strip()
                    if r in ['1', '2', '3', '4', '5']:
                        reason_dict['accept'].append(r)
            if reject_reason:
                reject_reason = reject_reason.group(1).split(',')
                reason_dict['reject'] = []
                for r in reject_reason:
                    r = r.strip()
                    if r in ['1', '2', '3', '4', '5', '6', '7']:
                        reason_dict['reject'].append(r)
    
            # print(res)
            relative_path = os.path.relpath(file, base_dir)
            save_path = os.path.join(save_base_dir, relative_path)
            save_dir = os.path.dirname(save_path)
       
            # 首先找到原来目录的目录结构，然后在save_dir中按照该目录保存结果保存结果
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            with open(save_path, 'w') as f:
                json.dump(reason_dict, f, indent=4)

def convert_txt_to_json():
    base_dir = '/home/v-qinlinzhao/agent4reviews/simulated_review/classified_meta_review_reason'
    reason_count = {}
    reason_total_count = {'accept': {}, 'reject': {}}

    def process_directory(path, reason_dict):
        # 迭代path下的内容
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                # 如果是目录，递归处理
                reason_dict[item] = {}
                process_directory(item_path, reason_dict[item])
            elif item.endswith('.txt'):
                # 去除txt后缀
                item_name = item.replace('.txt', '')
                reason_dict[item_name] = {'accept': {}, 'reject': {}}
                # 如果是txt文件，处理文件内容
                with open(item_path, 'r') as f:
                    content = f.read()
                    # "Accept: 1,2,3; Reject: 3,4,7"
                    # 依据该字符串分别抽取Accept和Reject的原因
                    if 'Reject' in content:
                        accept_reason = re.search(r"Accept: (.+?);", content)
                    else:
                        accept_reason = re.search(r"Accept: (.+)", content)
                    reject_reason = re.search(r"Reject: (.+)", content)
                    # print(reject_reason)
                    if accept_reason:
                        accept_reason = accept_reason.group(1).split(',')
                        reason_dict[item_name]['accept'] = []
                        for r in accept_reason:
                            r = r.strip()
                            if r in ['1', '2', '3', '4', '5']:
                                if r not in reason_total_count['accept']:
                                    reason_total_count['accept'][r] = 0
                                reason_total_count['accept'][r] += 1
                                reason_dict[item_name]['accept'].append(r)
                    if reject_reason:
                        reject_reason = reject_reason.group(1).split(',')
                        reason_dict[item_name]['reject'] = []
                        for r in reject_reason:
                            r = r.strip()
                            if r in ['1', '2', '3', '4', '5', '6', '7']:
                                if r not in reason_total_count['reject']:
                                    reason_total_count['reject'][r] = 0
                                reason_total_count['reject'][r] += 1
                                reason_dict[item_name]['reject'].append(r)

    process_directory(base_dir, reason_count)

    # 将统计结果写入文件
    with open('reason.json', 'w') as f:
        json.dump(reason_count, f, indent=4)
    
    # 计算accept 和 reject中每一类原因的占比
    # reason_percentage = {'accept': {}, 'reject': {}}
    # for key, value in reason_total_count.items():
    #     total = sum(value.values())
    #     for k, v in value.items():
    #         reason_percentage[key][k] = v / total
        
    # with open('reason_count.json', 'w') as f:
    #     json.dump(reason_total_count, f, indent=4)
        
    # with open('reason_percentage.json', 'w') as f:
    #     json.dump(reason_percentage, f, indent=4)

def count_reasons():
    with open('../reason_result/reason.json', 'r') as f:
        reason_count = json.load(f)

    count = {}
    for year, year_dict in reason_count.items():
        count[year] = {}
        for model, model_dict in year_dict.items():
            count[year][model] = {}
            for type, type_dict in model_dict.items():
                count[year][model][type] = {}
                count[year][model][type]['accept'] = {}
                count[year][model][type]['reject'] = {}
                # 只在type层面做统计就好了
                for paper_id, paper_id_dict in type_dict.items():
                    for review_id, review_id_dict in paper_id_dict.items():
                        print(year, model, type, paper_id, review_id, review_id_dict)
                        # {'accept': {'1': 1, '2': 1, '5': 1}, 'reject': {'3': 1, '4': 1, '5': 1, '7': 1}}
                        if 'accept' in review_id_dict:
                            for accept_reason in review_id_dict['accept']:
                                if accept_reason not in count[year][model][type]['accept']  \
                                                and accept_reason in ['1', '2', '3', '4', '5']:
                                    count[year][model][type]['accept'][accept_reason] = 0
                                count[year][model][type]['accept'][accept_reason] += 1
                        if 'reject' in review_id_dict: 
                            for reject_reason in review_id_dict['reject']:
                                if reject_reason not in count[year][model][type]['reject'] \
                                                and reject_reason in ['1', '2', '3', '4', '5', '6', '7']:
                                    count[year][model][type]['reject'][reject_reason] = 0
                                count[year][model][type]['reject'][reject_reason] += 1   

    with open('reason_count.json', 'w') as f:
        json.dump(count, f, indent=4)

def calcu_reason_percentage_every_year():
    with open('../reason_result/reason_count.json', 'r') as f:
        reason_count = json.load(f)

    distribution = {}
    for year, year_dict in reason_count.items():
        distribution[year] = {}
        for model, model_dict in year_dict.items():
            distribution[year][model] = {}
            for type, type_dict in model_dict.items():
                distribution[year][model][type] = {}
                distribution[year][model][type]['accept'] = {}
                distribution[year][model][type]['reject'] = {}
                # 统计百分比，先将accept下面的count加起来，然后得到每个百分比
                accept_sum = sum(type_dict['accept'].values())
                for reason, count in type_dict['accept'].items():
                    distribution[year][model][type]['accept'][reason] = count / accept_sum
                reject_sum = sum(type_dict['reject'].values())
                for reason, count in type_dict['reject'].items():
                    distribution[year][model][type]['reject'][reason] = count / reject_sum
    
    with open('reason_percentage.json', 'w') as f:
        json.dump(distribution, f, indent=4)
 
def calcu_reason_percentage():
    # 以每种类别为单位，计算每种类别下的accept和reject的百分比
    with open('../reason_result/reason_count.json', 'r') as f:
        reason_count = json.load(f)
        
    count_dict = {}
    for year, year_dict in reason_count.items():
        for model, model_dict in year_dict.items():
            for type, type_dict in model_dict.items():
                count_dict[type] = {'accept': {}, 'reject': {}}
                # 得到所有year和model的accept和reject的count
                accept_count = type_dict['accept']
                reject_count = type_dict['reject']
                # 将accept中每一类原因进行累加
                for reason, count in accept_count.items():
                    if reason not in count_dict[type]['accept']:
                        count_dict[type]['accept'][reason] = 0
                    count_dict[type]['accept'][reason] += count
                for reason, count in reject_count.items():
                    if reason not in count_dict[type]['reject']:
                        count_dict[type]['reject'][reason] = 0
                    count_dict[type]['reject'][reason] += count
    # 计算count_dict中accept和reject其中原因的百分比
    reason_percentage = {}
    for type, type_dict in count_dict.items():
        reason_percentage[type] = {'accept': {}, 'reject': {}}
        accept_sum = sum(type_dict['accept'].values())
        for reason, count in type_dict['accept'].items():
            reason_percentage[type]['accept'][reason] = count / accept_sum
        reject_sum = sum(type_dict['reject'].values())
        for reason, count in type_dict['reject'].items():
            reason_percentage[type]['reject'][reason] = count / reject_sum
    
    with open('reason_percentage.json', 'w') as f:
        json.dump(reason_percentage, f, indent=4)

def draw_bar_chart(accept_or_reject, ax, type, name1, name2):
    # accept_or_reject = 'accept'
    
    x = {
        "accept": ['Novelty', 'Significance', 'Theoretical', 'Clarity', 'Future'],
        "reject": ['Novelty', 'Theoretical', 'Validation', 'Practicality', 'Limitations', 'Presentation', 'Related Work']
    }
    x_range = range(1, len(x[accept_or_reject])+1)
    
    # 画出每一年的type1 和 type2两种type的比例图
    with open('../reason_result/reason_percentage.json', 'r') as f:
        reason_percentage = json.load(f)
    
        # 取出其中的type1和type2两种type
        type1 = reason_percentage[name1][accept_or_reject]
        type2 = reason_percentage[name2][accept_or_reject]
        
        # 按照key排序
        type1 = dict(sorted(type1.items(), key=lambda x: int(x[0])))
        type2 = dict(sorted(type2.items(), key=lambda x: int(x[0])))
        # dict中key应该是1-7，如果有的Key没有，就加上这个key，value设置为0
        for i in x_range:
            if str(i) not in type1:
                type1[str(i)] = 0
            if str(i) not in type2:
                type2[str(i)] = 0
        
        width = 0.35  # 柱子的宽度
        
        # fig, ax = plt.subplots()
        ax.bar([i - width/2 for i in x_range], type1.values(), width, label=name1, color=COLORS[0], alpha=0.3)
        ax.bar([i + width/2 for i in x_range], type2.values(), width, label=name2, color=COLORS[1], alpha=0.3)
        
        ax.legend()
        ax.set_xlabel('Reason', fontsize=FONT_SIZE)
        # ax.set_ylabel('Percentage', fontsize=FONT_SIZE)
        ax.set_title(type, fontsize=FONT_SIZE)
        ax.set_xticks(x_range)  # 设置x轴刻度为整数
        ax.set_xticklabels(x[accept_or_reject], rotation=30)
        
        # plt.savefig(f'reason_distribution_{type}.png')
        # plt.close()                  
                
def draw_bar_chart_baseline(ax, baseline_or_ground, accept_or_reject):
    # if baseline_or_ground == 'Baseline':
    #     with open('../simulated_review/reason_result/reason_percentage.json', 'r') as f:
    #         reason_percentage = json.load(f)
    #         type_data = reason_percentage['BASELINE'][accept_or_reject]
    # elif baseline_or_ground == 'Ground Truth':
    with open('reason_percentage.json', 'r') as f:
        reason_percentage = json.load(f)
        type_data = reason_percentage[baseline_or_ground][accept_or_reject]
    
    
    x = {
        "accept": ['Novelty', 'Significance', 'Theoretical', 'Clarity', 'Future'],
        "reject": ['Novelty', 'Theoretical', 'Validation', 'Practicality', 'Limitations', 'Presentation', 'Related Work']
    }
    x_range = range(1, len(x[accept_or_reject])+1)
        
    # 按照key排序
    type_data = dict(sorted(type_data.items(), key=lambda x: int(x[0])))
    
    # dict中key应该是1-7，如果有的Key没有，就加上这个key，value设置为0
    for i in x_range:
        if str(i) not in type_data:
            type_data[str(i)] = 0
    
    # 画图，将单一类型画到图上，选取颜色，设置透明度
    width = 0.35  # 柱子的宽度
    
    # fig, ax = plt.subplots()
    ax.bar(x_range, type_data.values(), width, label=accept_or_reject, color=COLORS[0], alpha=0.7)
    
    ax.legend()
    ax.set_xlabel('Reason', fontsize=FONT_SIZE)
    # ax.set_ylabel('Percentage', fontsize=FONT_SIZE)
    ax.set_title(baseline_or_ground, fontsize=FONT_SIZE)
    ax.set_xticks(x_range)  # 设置x轴刻度为整数
    ax.set_xticklabels(x[accept_or_reject], rotation=30)
    
    # plt.savefig(f'{baseline_or_ground}_{accept_or_reject}_reason_distribution.pdf')
    # plt.close()

def draw_reason_distribution(accept_or_reject):
    type2name = {'accept': 'Acceptance', 'reject': 'Rejection'}
    
    fig, axs = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f'Distribution of {type2name[accept_or_reject]} Reasons', fontsize=FONT_SIZE)
    
    # authoritarian_ACx1 inclusive_ACx1 conformist_ACx1
    draw_bar_chart_baseline(axs[0], 'authoritarian_ACx1', accept_or_reject)
    draw_bar_chart_baseline(axs[1], 'inclusive_ACx1', accept_or_reject)
    draw_bar_chart_baseline(axs[2], 'conformist_ACx1', accept_or_reject)
    
    # draw_bar_chart_baseline(axs[0], 'Baseline', accept_or_reject)
    # draw_bar_chart_baseline(axs[1], 'Ground Truth', accept_or_reject)
    
    # for i, (key, value) in enumerate(types.items()):
    #     if i == 3:
    #         break
    #     draw_bar_chart(accept_or_reject, axs[i], key, value[0], value[1])

    axs[0].set_ylabel('Percentage', fontsize=FONT_SIZE)
    
    plt.tight_layout()
    plt.savefig(f'reason_distribution_AC_{accept_or_reject}.pdf')
    plt.close()
        

if __name__ == "__main__":
    # analysis_pipeline()
    # convert_txt_to_json()
    draw_reason_distribution('reject')
    
    
# if __name__ == "__main__":
#     # get current path
#     # print(os.getcwd())
#     print("Start analysis...")
        
#     json_files = []
#     for root, dirs, files in os.walk(base_dir):
#         for file in files:
#             if file.endswith('.json'):
#                 json_files.append(os.path.join(root, file))
    
#     # json_files = [f for f in json_files]
#     # print(json_files)
    
#     # 将其平均分为6份，每份分配给一个进程
#     n = len(json_files)
#     n_per_process = n // 6
#     processes = []
#     for i in range(6):
#         start = i * n_per_process
#         end = (i + 1) * n_per_process
#         if i == 5:
#             end = n
#         p = multiprocessing.Process(target=analyze_reason_in_batch, args=(json_files[start:end], ))
#         processes.append(p)
#         p.start()
    