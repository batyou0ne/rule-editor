import { StreamLanguage, HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { tags as t } from "@lezer/highlight";

// Ported from https://gitlab.com/eflint/tools/syntax-highlighting-vscode
// (syntaxes/eflint.tmLanguage.json) — same token groups, order preserved
// so ambiguous prefixes (e.g. "Violated when" vs "Violated") resolve the same way.

const MACRO = /^#(include|require)\b/;

const KEYWORDS = /^\b(Fact|Placeholder|Predicate|Invariant|Event|Act|Duty|Extend|Open|Closed)\b/;

const KEYWORD_PHRASES =
  /^\b(Identified by|Actor|Recipient|Holder|Claimant|Created by|Obfuscated by|Terminated by|Violated when|Violated|Related to|Syncs with|Holds when|Derived from|Derived externally|Conditioned by|Enforced by|Creates|Obfuscated|Terminates)\b/;

const OPERATOR_WORDS = /^\b(Not|Foreach|Exists|Forall|Force|Do|Sum|Count|Max|Min|When|Union|Enabled)\b/;

const OPERATOR_SYMBOLS = /^(\?-|!\?|==|!=|<=|>=|\|\||&&|[+\-*/?!.<>])/;

const BOOL = /^\b(true|false|True|False)\b/;

const NUMBER = /^-?[0-9]+\b/;

const BUILTIN = /^\b(Current Time|String|Int|Bool|Boolean|Time|Atom)\b/;

const TYPED_VAR = /^\b(string|int|bool)\b/;

const BRACKETED_NAME = /^\[[A-Za-z_][A-Za-z0-9_\- ]*\]/;

const LOWER_IDENT = /^[a-z_][A-Za-z0-9\-_]*/;

// "implicit-strings" in the TextMate grammar — capitalized identifiers used
// as bare string values (agent/act instance names etc).
const UPPER_IDENT = /^[A-Z][A-Za-z0-9\-_]*/;

function token(stream) {
  if (stream.match("//")) {
    stream.skipToEnd();
    return "comment";
  }
  if (stream.eatSpace()) return null;

  if (stream.match(MACRO)) return "macroName";
  if (stream.match(KEYWORD_PHRASES)) return "keyword";
  if (stream.match(KEYWORDS)) return "keyword";
  if (stream.match(OPERATOR_WORDS)) return "operatorKeyword";
  if (stream.match(BOOL)) return "atom";
  if (stream.match(NUMBER)) return "number";
  if (stream.match(BUILTIN)) return "typeName";
  if (stream.match(TYPED_VAR)) return "typeName";

  if (stream.match('"', true)) {
    while (!stream.eol()) {
      if (stream.match(/^\\[\\'"trn]/)) continue;
      if (stream.next() === '"') break;
    }
    return "string";
  }

  if (stream.match(OPERATOR_SYMBOLS)) return "operator";
  if (stream.match(BRACKETED_NAME)) return "variableName";
  if (stream.match(UPPER_IDENT)) return "className";
  if (stream.match(LOWER_IDENT)) return "variableName";

  stream.next();
  return null;
}

export const eflintLanguage = StreamLanguage.define({ token });

export const eflintHighlightStyle = HighlightStyle.define([
  { tag: t.comment, color: "#6a737d", fontStyle: "italic" },
  { tag: t.keyword, color: "#8250df", fontWeight: "600" },
  { tag: t.operatorKeyword, color: "#8250df" },
  { tag: t.macroName, color: "#953800" },
  { tag: t.atom, color: "#005cc5" },
  { tag: t.number, color: "#005cc5" },
  { tag: t.typeName, color: "#22863a" },
  { tag: t.string, color: "#032f62" },
  { tag: t.operator, color: "#d73a49" },
  { tag: t.variableName, color: "#24292e" },
  { tag: t.className, color: "#6f42c1" },
]);

export const eflintSyntaxExtensions = [eflintLanguage, syntaxHighlighting(eflintHighlightStyle)];
