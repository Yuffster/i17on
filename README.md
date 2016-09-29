# i17on
## Intranationalization

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

You can also call the script without installing by typing `python -m i17on`
from the root directory of this repository.

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

The debug mode can be enabled by using `--debug`, and will output the AST and
other helpful information for resolving issues with a particular input file,
or the library itself.

It can be placed before, after, or in the middle of tags.

```
i17on input.md --debug
```

## Syntax Documentation

### Dynamic tags

```
Hello {foo:foo}
```

If you pass this input into the main `i17on` executable with no arguments,
you'll get, "Hello".  If you also pass the argument `foo`, you'll get, 
"Hello foo"

| foo    | output        |
|--------|---------------|
| False  | Hello         |
| True   | Hello foo     |

This is because `foo` is a boolean tag within the document, and passing the
`foo` argument sets its corresponding tag to True.

### Multiple conditions

```
Hello {foo:this is foo|-bar:this is bar|-world}.
```

| foo      | bar      | output                     |
|----------|----------|----------------------------|
| False    | False    | Hello, world.              |
| True     | False    | Hello, this is foo.        |
| False    | True     | Hello, this is bar.        |
| True     | True     | Hello, this is foo.        |

Notice that if `foo` and `bar` are True, it will output the conditional
branch for `foo` and stop before checking for other matching conditions.

This is very similar to a standard if/else statement.  For example, the
document above could also be described like this:

```python
if foo:
    print("foo")
elif bar:
    print("bar")
else:
	print("world")
```