import pyodbc
import csv

# 连接到 SQL Server 数据库
conn_str = 'DRIVER={SQL Server}; SERVER=DESKTOP-DKRFPTD\SQLEXPRESS; DATABASE=SalesPrediction'
conn = pyodbc.connect(conn_str)

# 创建游标对象
cursor = conn.cursor()

keyword = input("请输入要查询的商品：")

# 定义SQL查询
query = f"""
    WITH RankedData AS (
    SELECT 
        report_date,
        keyword,
        ranks,
        LAG(ranks, 1) OVER (PARTITION BY keyword ORDER BY report_date) AS prev_ranks,
        LEAD(ranks, 1) OVER (PARTITION BY keyword ORDER BY report_date) AS next_ranks 
    FROM SalesPrediction.dbo.TestData
)
SELECT 
    report_date
FROM 
    RankedData
WHERE 
    keyword = '{keyword}'
    AND prev_ranks IS NOT NULL
    AND next_ranks IS NOT NULL
    AND (next_ranks - ranks) / NULLIF((ranks - prev_ranks), 0) < 0 
	AND ABS(next_ranks - ranks) > 5000;

    """

cursor.execute(query)

# 获取查询结果
result = cursor.fetchall()

# 输出结果
for row in result:
    print(row)

# 关闭游标和连接
cursor.close()
conn.close()

# Agent部分
import os
#设置API密钥
os.environ["GROQ_API_KEY"] = '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'
os.environ["SERPAPI_API_KEY"] = 'bf9be960ab41626e4c2d77e54ea476e6506c7c2bbece6a3bd976cf1b5e5bb2cf'

from langchain import hub
#获取React提示
prompt=hub.pull("hwchase17/react")

# 导入大模型
from langchain_groq import ChatGroq

# 初始化 Anthropic 模型
llm = ChatGroq(model_name="llama3-8b-8192",temperature=0.7)

from langchain_community.utilities import SerpAPIWrapper
from langchain.agents.tools import Tool
search = SerpAPIWrapper()

#准备工具列表
tools = [
    Tool(
        name = 'Search',
        func = search.run,
        description = '当大模型没有相关知识时，用于搜索知识'
    )

]

from langchain.agents import create_react_agent
agent = create_react_agent(llm, tools, prompt)

from langchain.agents import AgentExecutor
agent_executor = AgentExecutor(agent=agent,tools=tools,verbose=True,handle_parsing_errors=True)

# 将keyword 和 final_answer写入表格中
def write(keyword,final_answer):
    with open('E:\FastFind.AI\工作薄2.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        #writer.writerow(['Keyword', 'Final Answer'])
        writer.writerow([keyword, final_answer])

def main():
    user_input = keyword+'这个商品在'.join([str(row[0]) for row in result])+'在这个日期发生了销量突变。请查询一下是什么事件导致了这个销量突变？' #改成循环
    Ag_result = agent_executor.invoke({"input": user_input})
    # print(result)

# 从结果中分离出final answer
    output_str = Ag_result.get('output', '')
    if "Final Answer:" in output_str:
        final_answer = output_str.split("Final Answer:")[-1].strip()
    else:
        final_answer = output_str

    print(final_answer)

    write(keyword, final_answer) #调用写入csv的函数

if __name__ == "__main__":
    main()




