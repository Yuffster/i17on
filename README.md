# Intranationalization (i17on)

i17on is a text preprocessor which allows you to write dynamic documents using a simple tag-based language.

You can write your document once in i17on, then disable and enable tags as necessary to tailor the text to a wide variety of target audiences.

i17on intelligently ensures that the whitespace of your document is normalized for English sentences and paragraphs.  It's also Markdown-aware, meaning that you can include lists, code, headings, *bold* and _italicised_ text, and many other features which will work in the way you expect.

Other formats can also be used, such as HTML.

Currently the output of the compiler is provided as the raw processed document, which can be sent to other libraries such as pandoc for proper
formatting.

## Installation

### From Git

```
git checkout git@github.com:Yuffster/i17on.git
cd i17on
python setup.py install
```

### Using Pip

```
pip install i17on
```

## Usage

The setup.py script will provide you with an i17on command.

You can also call the script without installing by typing `python -m i17on` from the root directory of this repository.

The `i17on` command takes the input file as its first parameter.  The rest of the parameters are a list of tags which will be set to `True` for the purpose of output generation.

```
i17on input.md foo bar bizz
```

### stdin

You can also use stdin instead.

```
cat input.md | i17on foo bar bizz
```

### debug

The debug mode can be enabled by using `--debug`, and will output the AST and other helpful information for resolving issues with a particular input file, or the library itself.

It can be placed before, after, or in the middle of tags.

```
i17on input.md --debug
```

## Syntax Documentation

### Dynamic tags

The most basic syntax of i17on is to use a tag, marked by curly braces.

The string of text preceeding the colon is the conditional, in this case just one tag.  The text will show up if foo is set to true.

```
Hello {foo:world}
```

If you pass this input through i17on, you'll get the following output, based on whether or not the `foo` tag is set.

| foo    | output        |
|--------|---------------|
| False  | Hello         |
| True   | Hello world   |

### Branches

Additional conditionals can be added to a single tag by using the `|-` (branch) separator.

```
Hello {foo:this is foo|-bar:this is bar}.
```

This is very similar to a standard if/else statement.  For example, the document above could also be described like this:

```python
if foo:
    print("foo")
elif bar:
    print("bar")
```

| foo      | bar      | output                     |
|----------|----------|----------------------------|
| False    | False    | Hello.                     |
| True     | False    | Hello this is foo.         |
| False    | True     | Hello this is bar.         |
| True     | True     | Hello this is foo.         |

Notice that if `foo` and `bar` are True, it will output the conditional branch for `foo` and stop before checking for other matching conditions.

### Default branches

If no condition is provided for a branch, it will always be evaluated as True.  This allows you to add a default branch to be executed if none of the preceding conditions are True.

```
Hello {foo:this is foo|-bar:this is bar|-world}.
```

| foo      | bar      | output                     |
|----------|----------|----------------------------|
| False    | False    | Hello world.               |
| True     | False    | Hello this is foo.         |
| False    | True     | Hello this is bar.         |
| True     | True     | Hello this is foo.         |

If we move the default statement to the middle of our tag, we'll get "Hello world" regardless of the value of `bar`.

```
Hello {foo:this is foo|-world|-bar:this is bar}.
```

| foo      | bar      | output                     |
|----------|----------|----------------------------|
| False    | False    | Hello world.               |
| True     | False    | Hello this is foo.         |
| False    | True     | **Hello world.**           |
| True     | True     | Hello this is foo.         |

### Conditional Clauses

#### AND

You can combine conditions using a comma, in which case all of them have to be True.  For example, `foo,bar` is analogous to `if foo and bar` in normal code.

```
Hello {foo,bar:foo and bar}
```

| foo      | bar      | output                     |
|----------|----------|----------------------------|
| False    | False    | Hello                      |
| True     | False    | Hello                      |
| False    | True     | Hello                      |
| True     | True     | Hello foo and bar          |

This is analogous to saying `if foo and bar` in normal code.

#### OR

You can combine conditional clauses using the semicolon operator, in which case all of them have to be True.  

`foo;bar` is analogous to `if foo or bar`, and `foo,bar;bizz` is analogous to `if (foo and bar) or (bizz)`.
 
```
Hello {foo;bar:foo or bar}
```

| foo      | bar      | output                     |
|----------|----------|----------------------------|
| False    | False    | Hello                      |
| True     | False    | Hello foo or bar           |
| False    | True     | Hello foo or bar           |
| True     | True     | Hello foo or bar           |

#### Negation

Prepending a tag with an exclaimation point (!) will negate that tag.

```
Hello {foo,!bar:foo and not bar}
```

| foo      | bar      | output                     |
|----------|----------|----------------------------|
| False    | False    | Hello                      |
| True     | False    | Hello foo and not bar      |
| False    | True     | Hello                      |
| True     | True     | Hello                      |

### Whitespace

In a more complex document, you might want to nest arbitrary whitespace.  The compiler is designed to intelligently discard unnecessary spacing.

Here, we have more readable spacing, which will produce the same output as our earlier example.

Work is ongoing to ensure that the compiled document conforms to expectations concerning English grammar, as well as Markdown specifics, such as indented lists and code examples.

```
Hello {
	foo:
		this is foo
	|-bar:
	    this is bar
	|-
		world
}.
```

| foo      | bar      | output                     |
|----------|----------|----------------------------|
| False    | False    | Hello world.               |
| True     | False    | Hello this is foo.         |
| False    | True     | Hello this is bar.         |
| True     | True     | Hello this is foo.         |

### Nesting

Tags can be nested within other tags.

```
Hello {
	foo:
		this is foo {bar:and bar}
	|-
		world
}.
```

| foo      | bar      | output                     |
|----------|----------|----------------------------|
| False    | False    | Hello world.               |
| True     | False    | Hello this is foo.         |
| False    | True     | Hello this is bar.         |
| True     | True     | Hello this is foo and bar. |

