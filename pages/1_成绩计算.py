import pdfplumber
import tempfile
import streamlit as st
import pandas as pd
from PIL import Image
import base64
import xlsxwriter as xw
import io


icon_path = "images/院徽.ico"

ICON = Image.open(icon_path)
with open(icon_path, "rb") as img_file:
    ICON_base64 = base64.b64encode(img_file.read()).decode()

st.set_page_config(
    page_title="辅导猿-成绩计算",
    layout="centered",
    page_icon=ICON,
)


with st.sidebar:
    icon_text = f"""
        <div class="icon-text-container" style="text-align: center;">
            <img src='data:image/png;base64,{ICON_base64}' alt='icon' style='width: 70px; height: 70px; margin: 0 auto; display: block;'>
            <span style='font-size: 24px;'>辅导猿-学生日常事务管家</span>
        </div>
        """
    st.markdown(
        icon_text,
        unsafe_allow_html=True,
    )



st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)

st.title("💯 智课灵犀")
st.caption("🌈 成绩统计小工具（声明：本程序对转专业同学以及留级同学的存在考虑不周的情况！）")
print('声明：本程序对转专业同学以及留级同学的存在考虑不周的情况！\n')

# 定义全局变量以存储成绩数据
cj = []


# 判断是否为数字
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False


# 计算成绩的函数
def count_score(pdf_data, cla_list, term=None):
    global cj
    dict = {"优": 92.5, "良": 80, "中": 69.5, "及格": 62, '不及\n格': 30, '缺考': 0, '其它': 0, '缓考': 0}
    sum_score = 0  # 各个课程分数乘上对应学分后的总分数
    sum_score2 = 0  # 总分数
    sum_credit = 0  # 总学分
    sum_num = 0  # 课程总数量

    with pdfplumber.open(pdf_data) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            name_st = text.find('名') + 2
            name_end = text.find('号') - 2
            id_pos = text.find('号') + 2

            for table in page.extract_tables():
                for row in table:
                    if row[1] in cla_list and ((not term) or (row[4] in term)):
                        sum_credit += float(row[2])
                        sum_num += 1
                        if is_number(row[3]):
                            sum_score2 += float(row[3])
                            sum_score += float(row[3]) * float(row[2])
                        else:
                            sum_score2 += dict.get(row[3], 0)
                            sum_score += dict.get(row[3], 0) * float(row[2])

                    if row[6] in cla_list:
                        sum_credit += float(row[7])
                        sum_num += 1
                        if is_number(row[8]):
                            sum_score2 += float(row[8])
                            sum_score += float(row[8]) * float(row[7])
                        else:
                            sum_score2 += dict.get(row[8], 0)
                            sum_score += dict.get(row[8], 0) * float(row[7])

            cj.append({
                '姓名': text[name_st:name_end],
                '学号': text[id_pos:(id_pos + 12)],
                '加权平均': round(sum_score / sum_credit, 3) if sum_credit else 0,
                '平均': round(sum_score2 / sum_num, 3) if sum_num else 0,
            })


def process_pdf(uploaded_file, cla_list, term):
    try:
        count_score(uploaded_file, cla_list, term)
    except Exception as e:
        st.error(f"处理文件时发生错误: {str(e)}")
        return None


def generate_csv(data):
    df = pd.DataFrame(data)
    df['学号'] = df['学号'].astype(str)
    return df.to_csv(index=False).encode('gbk')


def main():
    cla = st.radio('请选择成绩统计类型：', ('专业必修成绩', '专业必修+专业选修成绩'))
    cla_list = ["必修"] if cla == '专业必修成绩' else ["必修", "选修"]

    term_input = st.text_input("请输入你要统计的学期，用空格隔开，如\"5 6 7\"，为空则默认统计所有学期。")
    term = term_input.split() if term_input else []
    term.sort()
    term_str = '_'.join(term) if term else ""

    uploaded_files = st.file_uploader("上传 学生个人成绩表.pdf", type=['pdf'], accept_multiple_files=True)

    if st.button('计算'):
        global cj
        cj = []  # 清空之前的结果
        for uploaded_file in uploaded_files:
            process_pdf(uploaded_file, cla_list, term)

        if cj:
            output = io.BytesIO()  # 创建一个字节流
            workbook = xw.Workbook(output, {'in_memory': True})
            worksheet1 = workbook.add_worksheet("sheet1")  # 创建子表

            title = ['姓名', '学号', '加权平均', '平均']
            worksheet1.write_row('A1', title)  # 从A1单元格开始写入表头

            i = 2  # 从第二行开始写入数据
            for j in range(len(cj)):
                insertData = [cj[j]["姓名"], cj[j]["学号"], cj[j]["加权平均"], cj[j]["平均"]]
                row = 'A' + str(i)
                worksheet1.write_row(row, insertData)
                i += 1

            workbook.close()
            output.seek(0)

            st.download_button(
                label="下载 成绩.xlsx" if term == [] else f"下载 {term_str}学期成绩.xlsx",
                data=output,
                file_name="成绩.xlsx" if term == [] else f"{term_str}学期成绩.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.write("未生成有效的成绩数据，请检查输入文件。")


if __name__ == "__main__":
    main()
