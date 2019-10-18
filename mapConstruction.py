import requests
import re
import json
from progressbar import *
from py2neo import Graph, Node, Relationship, NodeMatcher
graph = Graph(
    "http://localhost:7474",
    username="neo4j",
    password="neo4j"
)

def Add_Entity(name, attrs):
	a = Node(name, **attrs)
	# 同样的实体不会新建两次
	matcher = NodeMatcher(graph)
	temp = matcher.match(name,subname=attrs['subname']).first()
	if temp is None:
		graph.create(a)

def Add_Relation(n1, rela, n2):
    re = Relationship(n1, rela, n2)
    graph.merge(re)


def Get_Graph_Result_By_Api(keyword ='北京航空航天大学'):

	# 获取keyword搜索得到的知行数据库的图谱(由多个关联实体组成的局部图谱)
	url = 'http://www.actkg.com/api/robot/talk/?q={}'.format(keyword)
	headers = {'Accept': 'text/html, application/xhtml+xml, image/jxr, */*',
               'Accept - Encoding':'gzip, deflate',
               'Accept-Language':'zh-Hans-CN, zh-Hans; q=0.5',
               'Connection':'close',
               'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063'}
	response = requests.get(url,timeout=3,headers=headers)
	html = response.content.decode('utf-8', errors='ignore')
	# Unicode码转为中文
	graph_result = html.encode('latin-1').decode('unicode_escape')
	graph_result = json.loads(graph_result)

	return graph_result

def Get_Entity_By_Api(neoId):

	# 根据知行数据库中的neoId获取该实体的全部属性
	url = 'http://www.actkg.com/api/graph/entity/?id={}'.format(neoId)
	headers = {'Accept': 'text/html, application/xhtml+xml, image/jxr, */*',
               'Accept - Encoding':'gzip, deflate',
               'Accept-Language':'zh-Hans-CN, zh-Hans; q=0.5',
               'Connection':'close',
               'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063'}
	response = requests.get(url,timeout=3,headers=headers)
	html = response.content.decode('utf-8', errors='ignore')
	entity = "".join(html.split())
	entity = json.loads(entity)

	return entity

if __name__=="__main__":
	graph_result = Get_Graph_Result_By_Api()
	all_nodes = graph_result['nodes']
	all_relations = graph_result['links']
	pbar = ProgressBar().start()
	total = len(all_nodes) + len(all_relations)
	print("正在创建知行系统原局部知识图谱...")
	# 创建原始实体
	for i, node in enumerate(all_nodes):
		entity_property = Get_Entity_By_Api(node['neoId'])
		Add_Entity(node['name'], entity_property)
		# 显示进度条
		pbar.update(int((i / (total - 1)) * 100))

	# 创建原始关系
	matcher = NodeMatcher(graph)
	for i, relation in enumerate(all_relations):
		source_label = all_nodes[relation['source']]['name']
		source_node = matcher.match(source_label).first()
		target_label = all_nodes[relation['target']]['name']
		target_node = matcher.match(target_label).first()
		Add_Relation(source_node, relation['name'], target_node)
		# 显示进度条
		pbar.update(int(((i+len(all_nodes)) / (total - 1)) * 100))

	print("done!")
