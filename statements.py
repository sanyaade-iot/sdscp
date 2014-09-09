#!/bin/env python3

import re

from tokens import *
import expressions
from expressions import *
from utils import SyntaxNode


def parse(tokens):
	""" Convert token list to a statement list. """

	tw = StTokenWalker(tokens)

	sx = []

	while tw.has_next():
		stmt = tw.consume_statement()
		sx.append(stmt)

	return sx



class StTokenWalker(TokenWalker):
	""" Token walker with support for collecting whole
	statements

	"""

	def consume_statement(self):
		""" Try to consume a statement, based on the current
		token (typically keyword)

		Returns:
			the statement

		"""

		# code block (used in structures)
		if self.has(T_CodeBlock):
			return S_Block(self)

		# empty statemenr
		if self.has(T_Semicolon):
			return S_Empty(self)

		# a function declaration
		if self.has(T_FUNCTION):
			return S_Function(self)

		# a function call
		if self.has(T_CALL):
			return S_Call(self)

		# return statement
		if self.has(T_RETURN):
			return S_Return(self)

		# GOTO statement
		if self.has(T_GOTO):
			return S_Goto(self)

		# LABEL
		if self.has(T_LABEL):
			return S_Label(self)

		# if-else
		if self.has(T_IF):
			return S_If(self)

		# a switch statement
		if self.has(T_SWITCH):
			return S_Switch(self)

		# a CASE
		if self.has(T_CASE):
			return S_Case(self)

		# a DEFAULT
		if self.has(T_DEFAULT):
			return S_Default(self)

		# while
		if self.has(T_WHILE):
			return S_While(self)

		# do-while
		if self.has(T_DO):
			return S_DoWhile(self)

		# for
		if self.has(T_FOR):
			return S_For(self)

		# break
		if self.has(T_BREAK):
			return S_Break(self)

		# continue
		if self.has(T_CONTINUE):
			return S_Continue(self)

		# var declaration
		if self.has(T_VAR):
			return S_Var(self)

		# var assignment
		if self.has(T_SET):
			return S_Assign(self)


		# ...

		# token not recognized
		raise Exception(
			'Could not create statement for token %s' %
			str(self.peek())
			)



class Statement(SyntaxNode):
	""" A syntactic unit

	A code piece that makes sense on it's own, and can be
	converted to source code if needed.

	"""

	def __str__(self):
		return type(self).__name__



class S_Empty(Statement):
	""" An empty statement (nop)

	Args:
		tw (TokenWalker): tw to collect the statement from

	"""

	def __init__(self, tw=None):
		super().__init__()

		if tw is not None:
			tw.consume(T_Semicolon)


	def __str__(self):
		return 'EMPTY'



class S_Comment(Statement):
	""" A comment to be rendered in the output source.
	Generated by the renderer / during preprocessing.

	Args:
		text (str): The comment text (can be multi-line)

	Attributes:
		text (str)

	"""

	def __init__(self, text):
		super().__init__()

		# declare instance attributes
		self.text = text


	def __str__(self):
		return '/* %s */' % self.text



class S_Goto(Statement):
	""" A goto statement. Will work only with label
	that is in the same function.

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		name (str):
			Name of the label to jump to.

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.name = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_GOTO)

		# the label name
		self.name = tw.consume(T_Name).value

		# a semicolon
		tw.consume(T_Semicolon)


	def __str__(self):
		return 'GOTO -> %s' % self.name



class S_Label(Statement):
	""" A label, goto target.

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		name (str):
			Name of the label. Must be unique within the function.

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.name = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_LABEL)

		# the label name
		self.name = tw.consume(T_Name).value

		# a colon
		tw.consume(T_Colon)


	def __str__(self):
		return 'LABEL: %s' % self.name



class S_Call(Statement):
	""" Function call, discarding the return value.

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		name (str): function name
		args (Expression[]): list of argument values

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.name = None
		self.args = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_CALL)

		# func name
		self.name = tw.consume(T_Name).value

		# arguments paren
		paren = tw.consume_paren(ParenType.ARGVALS)

		# collect all argument names
		atw = StTokenWalker(paren.tokens)
		self.args = []
		while atw.has_next():
			val = atw.consume(T_Expression)

			expr = expressions.parse(val)
			self.args.append(expr)

		tw.consume(T_Semicolon)


	def _bind_children(self):
		for a in self.args:
			a.bind_parent(self)


	def __str__(self):
		s = 'CALL %s' % self.name
		s += '(%s)' % ', '.join( [str(a) for a in self.args] )

		return s



class S_Function(Statement):
	""" A function statement

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		name (str): function name
		args (str[]): list of argument names
		body_st (S_Block): a function body

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.name = None
		self.args = None
		self.body_st = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_FUNCTION)

		# func name
		self.name = tw.consume(T_Name).value

		# arguments paren
		paren = tw.consume_paren(ParenType.ARGNAMES)

		# collect all argument names
		atw = StTokenWalker(paren.tokens)
		self.args = []
		while atw.has_next():
			n = atw.consume(T_Name).value
			self.args.append(n)

		# get function body
		self.body_st = S_Block(tw)


	def _bind_children(self):
		self.body_st.bind_parent(self)


	def __str__(self):
		s = 'FUNC %s' % self.name
		s += '(%s)' % ', '.join( [str(a) for a in self.args] )
		s += ' %s' % str(self.body_st)

		return s



class S_Return(Statement):
	""" A return statement

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		value (Expression): The return value

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.value = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_RETURN)

		if tw.has(T_Expression):
			# explicitly given return value
			expr = tw.consume(T_Expression)
			self.value = expressions.parse(expr)
		else:
			# a defualt return value
			self.value = E_Literal(T_Number('0'))

		tw.consume(T_Semicolon)


	def _bind_children(self):
		self.value.bind_parent(self)


	def __str__(self):
		return 'RETURN %s' % str(self.value)



class S_Case(Statement):
	""" A case in switch.

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		value (Expression):
			The case value (compared to the switch value)

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.value = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_CASE)

		# the value
		expr = tw.consume(T_Expression)
		self.value = expressions.parse(expr)

		# a colon
		tw.consume(T_Colon)


	def _bind_children(self):
		self.value.bind_parent(self)


	def __str__(self):
		return 'CASE %s' % str(self.value)



class S_Default(Statement):
	""" A Default in switch. """

	def __init__(self, tw=None):
		super().__init__()

		# keyword
		tw.consume(T_DEFAULT)

		# a colon
		tw.consume(T_Colon)


	def __str__(self):
		return 'DEFAULT'



class S_Break(Statement):
	""" A break statement, used in loops and switch.

	Args:
		tw (TokenWalker): tw to collect the statement from

	"""

	def __init__(self, tw=None):
		super().__init__()

		# keyword
		tw.consume(T_BREAK)

		# a semicolon
		tw.consume(T_Semicolon)


	def __str__(self):
		return 'BREAK'



class S_Continue(Statement):
	""" A continue statement, used in loops.

	Args:
		tw (TokenWalker): tw to collect the statement from

	"""

	def __init__(self, tw=None):
		super().__init__()

		# keyword
		tw.consume(T_CONTINUE)

		# a semicolon
		tw.consume(T_Semicolon)


	def __str__(self):
		return 'CONTINUE'



class S_Block(Statement):
	""" A code block statement

	A block has it's own variable scope and can
	hold any number of child statements.

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		children (Statement[]): List of body statements

	"""

	def __init__(self, tw=None):
		super().__init__()

		self.children = []

		# allow creation without a TW
		if tw is None:
			return

		# keyword
		cb = tw.consume(T_CodeBlock)

		# code-block token walker
		ctw = StTokenWalker(cb.tokens)

		# collect all child statements
		while ctw.has_next():
			st = ctw.consume_statement()

			# add if not an empty statement
			if not isinstance(st, S_Empty):
				self.children.append(st)


	def _bind_children(self):
		for s in self.children:
			s.bind_parent(self)


	def __str__(self):
		return 'BLOCK {\n%s\n}' % (
			'\n'.join([str(s) for s in self.children]))



class S_Var(Statement):
	""" A variable declaration.

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		var (E_Variable): the variable name
		value (Expression): the initial value

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.var = None
		self.value = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_VAR)

		# variable name
		name = tw.consume(T_Name).value
		self.var = E_Variable(name)

		# optional rvalue
		if tw.has(T_Rvalue):

			# operator and value
			rv = tw.consume(T_Rvalue)
			assignOp = rv.tokens[0]
			expr = rv.tokens[1]

			# cannot use other than simple = in declaration
			# the variable isn't defined yet.
			if assignOp.value != '=':
				raise Exception(
					'Cannot use %s in variable declaration!'
					% assignOp.value
				)

			self.value = expressions.parse(expr)

		else:
			# synthetic zero value
			self.value = None

		tw.consume(T_Semicolon)


	def _bind_children(self):
		self.var.bind_parent(self)

		if self.value is not None:
			self.value.bind_parent(self)


	def __str__(self):
		if self.value is not None:
			return 'ALLOC %s = %s' % (self.var, str(self.value))
		else:
			return 'ALLOC %s' % self.var



class S_Assign(Statement):
	""" A variable assignment.

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		var (E_Variable): Assigned variable identifier
		op (T_AssignOperator): the assignment operator, eg. += or =
		value (Expression): the assigned value

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.var = None
		self.op = None
		self.value = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_SET)

		# variable name
		name = tw.consume(T_Name).value
		index = None
		if tw.has(T_Bracket):
			br = tw.consume(T_Bracket)
			index = br.index

		self.var = E_Variable(name, index)

		# operator and value
		rv = tw.consume(T_Rvalue)
		self.op = rv.tokens[0]

		# convert T_Expression to Expression
		self.value = expressions.parse( rv.tokens[1] )

		# end of statement
		tw.consume(T_Semicolon)


	def _bind_children(self):
		self.var.bind_parent(self)
		self.op.bind_parent(self)
		self.value.bind_parent(self)


	def __str__(self):
		return 'SET %s %s %s' % (self.var, self.op.value, str(self.value))



class S_If(Statement):
	""" If-else statement

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		cond (Expression): the branching condition
			goes to "true" branch if th condition is non-zero.
		then_st (Statement): the "true" statement
		else_st (Statement): the "false" statement

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.cond = None
		self.then_st = None
		self.else_st = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_IF)

		# paren with condition
		paren = tw.consume_paren(ParenType.EXPR)
		self.cond = expressions.parse( paren.expression )

		# the "then" branch
		self.then_st = tw.consume_statement()

		if tw.has(T_ELSE):
			# "else" branch
			tw.consume(T_ELSE)
			self.else_st = tw.consume_statement()
		else:
			# there is no "else" branch
			# add empty statement instead.
			self.else_st = S_Empty()


	def _bind_children(self):
		self.cond.bind_parent(self)
		self.then_st.bind_parent(self)
		self.else_st.bind_parent(self)


	def __str__(self):
		return 'IF (%s) THEN \n\t%s\nELSE\n\t%s\nENDIF' % (
			str(self.cond), str(self.then_st), str(self.else_st)
		)



class S_While(Statement):
	""" While loop

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		cond (Expression): the loop condition.
			Tested before each cycle.
		body_st (Statement): the loop body statement

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.cond = None
		self.body_st = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_WHILE)

		# paren with condition
		paren = tw.consume_paren(ParenType.EXPR)
		self.cond = expressions.parse( paren.expression )

		# the loop body
		self.body_st = tw.consume_statement()


	def _bind_children(self):
		self.cond.bind_parent(self)
		self.body_st.bind_parent(self)


	def __str__(self):
		return 'WHILE (%s) %s' % (
			str(self.cond), str(self.body_st)
		)



class S_DoWhile(Statement):
	""" Do-While loop

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		cond (Expression): the loop condition.
			Tested before each cycle.
		body_st (Statement): the loop body statement

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.cond = None
		self.body_st = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_DO)

		# the loop body
		self.body_st = tw.consume_statement()

		# keyword
		tw.consume(T_WHILE)

		# paren with condition
		paren = tw.consume_paren(ParenType.EXPR)
		self.cond = expressions.parse( paren.expression )

		# end of the statement.
		tw.consume(T_Semicolon)


	def _bind_children(self):
		self.cond.bind_parent(self)
		self.body_st.bind_parent(self)


	def __str__(self):
		return 'DO %s WHILE (%s);' % (
			str(self.body_st), str(self.cond)
		)



class S_For(Statement):
	""" For loop

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		init (Statement[]): the init statement
		cond (Expression): the loop condition;
			Tested before each cycle.
		iter (Statement[]): the iter statement;
			Executed after each cycle.
		body_st (Statement): the loop body statement

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.init = None
		self.cond = None
		self.iter = None
		self.body_st = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_FOR)

		# paren with init, cond, iter
		paren = tw.consume_paren(ParenType.FOR)
		self.cond = expressions.parse( paren.for_cond )

		# init statements
		itw = StTokenWalker(paren.for_init)
		self.init = []
		while itw.has_next():
			s = itw.consume_statement()
			self.init.append(s)

		# iter statements
		itw = StTokenWalker(paren.for_iter)
		self.iter = []
		while itw.has_next():
			s = itw.consume_statement()
			self.iter.append(s)

		# the loop body
		self.body_st = tw.consume_statement()


	def _bind_children(self):
		for s in self.init:
			s.bind_parent(self)

		self.cond.bind_parent(self)

		for s in self.iter:
			s.bind_parent(self)

		self.body_st.bind_parent(self)


	def __str__(self):
		return 'FOR ({%s}; %s; {%s}) %s' % (
			'; '.join([str(a) for a in self.init]),
			str(self.cond),
			'; '.join([str(a) for a in self.iter]),
			str(self.body_st)
		)



class S_Switch(Statement):
	""" Switch statement

	CASEs that are in the body's top level are part
	of this switch.

	Anywhere in the body can be used a BREAK statement
	to escape from the switch (of course, if it is nested
	in a loop or other switch, it has no effect on this
	main switch)

	Args:
		tw (TokenWalker): tw to collect the statement from

	Attributes:
		value (Expression): The switch value;
			The CASE values are compared with it.

		body_st (T_Block): The switch body.

	"""

	def __init__(self, tw=None):
		super().__init__()

		# declare instance attributes
		self.value = None
		self.body_st = None

		# if created without a TW
		if tw is None:
			return

		# keyword
		tw.consume(T_SWITCH)

		# paren with condition
		paren = tw.consume_paren(ParenType.EXPR)
		self.value = expressions.parse( paren.expression )

		# the switch body
		self.body_st = S_Block(tw)


	def _bind_children(self):
		self.value.bind_parent(self)

		self.body_st.bind_parent(self)


	def __str__(self):
		return 'SWITCH (%s) %s' % (
			str(self.value), str(self.body_st)
		)
