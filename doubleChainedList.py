class DCList: #Double Chained List
	def __init__(self,content, previous = None, next = None): # content : some_type, previous : DCList, next : DCList
		self.content = content
		self.previous = previous
		self.next = next
