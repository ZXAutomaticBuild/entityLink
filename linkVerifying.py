import re
import jieba
import jieba.posseg as posseg
from py2neo import Graph, Node, Relationship, NodeMatcher
graph = Graph(
    "http://localhost:7474",
    username="neo4j",
    password="neo4j"
)

def Find_Entity(name="北京航空航天大学"):
	results = graph.run("MATCH (n1:`{}`) RETURN n1".format(name)).data()
	return results[0]['n1']


def Find_Relative_Relations(node="北京航空航天大学"):
	results = graph.run("MATCH (n1:`{}`)-[r]->(n2) RETURN type(r),n2".format(node)).data()
	relations = []
	target_entitys = []
	for temp in results:
		relations.append(temp['type(r)'])
		target_entitys.append(temp['n2'])  
	return relations,target_entitys


def Similarity_Score(source_entity, relation, target_entity):
	keywords = set()
	score = 0
	# 属性名
	for item in posseg.cut(relation):
		if (item.flag == 'j') or (item.flag == 'l')or (item.flag[0] == 'n'):
			keywords.add(item.word)
	# 源实体名的j、l、nr、ns、nt、nz
	for item in posseg.cut(source_entity['name']):
		if (item.flag == 'j') or (item.flag == 'l')or ((item.flag[0] == 'n')and(len(item.flag)>1)):
			keywords.add(item.word)
	# 源实体的相关名称
	for key in source_entity.keys():
		if '名' in key[-1] or '简称' in key:
			# 中文字符模式
			zhmodel = re.compile(u'[\u4e00-\u9fa5]')
			# 找到所有中文字符
			match = zhmodel.findall(source_entity[key])
			# 拼接
			s = ''.join(match)
			# s为''则不保存
			if s:
				keywords.add(s)
	# 源实体的description中的属性值相关语句的j、l、nr、ns、nt、nz
	if source_entity[relation] in source_entity['description']:
		# 切段成句
		ls = source_entity['description'].split('。')
		for sentence in ls:
			# 属性值相关句子
			if source_entity[relation] in sentence:
				# 与属性值相关的有区分力的，词
				for item in posseg.cut(sentence):
					if (item.flag == 'j') or (item.flag == 'l')or ((item.flag[0] == 'n')and(len(item.flag)>1)):
						# 该词非属性值
						if item.word != source_entity[relation]:
							keywords.add(item.word)

	string_target_entity = ' '.join(target_entity.values())

	# 计算得分
	# print(keywords)
	for keyword in keywords:
		if keyword in string_target_entity:
			# print(keyword)
			score += 1

	return score

def Similarity_Score_C(source_entity, relation, target_entity):
	keywords = set()
	score = 0
	# 属性名
	for item in posseg.cut(relation):
		if (item.flag == 'j') or (item.flag == 'l')or (item.flag[0] == 'n'):
			keywords.add(item.word)
	# 源实体名的j、l、nr、ns、nt、nz
	for item in posseg.cut(source_entity['name']):
		if (item.flag == 'j') or (item.flag == 'l')or (item.flag[0] == 'n'):
			keywords.add(item.word)
	# 源实体的相关名称
	for key in source_entity.keys():
		if '名' in key[-1] or '简称' in key:
			# 中文字符模式
			zhmodel = re.compile(u'[\u4e00-\u9fa5]')
			# 找到所有中文字符
			match = zhmodel.findall(source_entity[key])
			# 拼接
			s = ''.join(match)
			# s为''则不保存
			if s:
				for item in posseg.cut(s):
					if (item.flag == 'j') or (item.flag == 'l')or (item.flag[0] == 'n'):
						keywords.add(item.word)
	# 源实体的description中的属性值相关语句的j、l、nr、ns、nt、nz
	if source_entity[relation] in source_entity['description']:
		# 切段成句
		ls = source_entity['description'].split('。')
		for sentence in ls:
			# 属性值相关句子
			if source_entity[relation] in sentence:
				# 与属性值相关的有区分力的，词
				for item in posseg.cut(sentence):
					if (item.flag == 'j') or (item.flag == 'l')or ((item.flag[0] == 'n')and(len(item.flag)>1)):
						# 该词非属性值
						if item.word != source_entity[relation]:
							keywords.add(item.word)

	string_target_entity = ' '.join(target_entity.values())

	# 计算得分
	# print(keywords)
	keywords_c = set()
	for keyword in keywords:
		keywords_c.update(jieba.cut(keyword, cut_all=True))
	# print(keywords_c)
	for keyword in keywords_c:
		if keyword in string_target_entity:
			# print(keyword)
			# n的权重是 0.35，其它的是 1 - 好像把事情搞复杂了；额；但能提高置性精度
			pair = list(posseg.cut(keyword))
			if pair[0].flag == 'n':
				score +=0.1
			elif pair[0].word in relation:
				score += 2
			else:
				score += 1

	return score

def Similarity_Score_Summary(source_entity, relation, target_entity):
	score_c = Similarity_Score_C(source_entity, relation, target_entity)
	score = Similarity_Score(source_entity, relation, target_entity)
	# score为 0 ,值得去否定
	# score为 0-2， 半肯定半否定
	# score为 >2，值得去肯定
	# 若为score_s，阈值变为2.8

	print("(",score,',',round(score_c,1),')',"：",source_entity['name'],'-',relation, '->', target_entity['name'])
	score_s = round((score_c ** 2+ score ** 2)**0.5, 1)
	if score_s >=2.8:
		print(score_s,'<值得肯定>')
	elif score_s == 0:
		print(score_s,'<该实体链接，值得否定>')
	else:
		print(score_s,'<半肯定半否定>')


if __name__=='__main__':
	# source_entity = Find_Entity()
	# source_entity = Find_Entity('中华人民共和国工业和信息化部')
	source_entity = Find_Entity('中华人民共和国')
	# source_entity = Find_Entity('中国')
	# source_entity = Find_Entity('材料科学与工程学院')
	# source_entity = Find_Entity('北京高科大学联盟')
	# source_entity = Find_Entity('知行合一')
	# source_entity = Find_Entity('德才兼备')
	# source_entity = Find_Entity('上海人民出版社')
	# source_entity = Find_Entity('美国')
	# source_entity = Find_Entity('芝加哥')
	# source_entity = Find_Entity('纽约')
	# source_entity = Find_Entity('汉族')
	relations, target_entitys = Find_Relative_Relations(source_entity['name'])
	for i in range(len(relations)):
		Similarity_Score_Summary(source_entity, relations[i], target_entitys[i])
		print("\n")