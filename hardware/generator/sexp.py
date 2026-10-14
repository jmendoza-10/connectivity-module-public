import re
def tokenize(s):
    i=0;n=len(s)
    while i<n:
        c=s[i]
        if c in ' \t\r\n': i+=1; continue
        if c=='(' or c==')': yield c; i+=1; continue
        if c=='"':
            j=i+1; buf=[]
            while s[j]!='"':
                if s[j]=='\\': c2=s[j+1]; buf.append({'n':'\n','t':'\t'}.get(c2,c2)); j+=2; continue
                buf.append(s[j]); j+=1
            yield ('S',''.join(buf)); i=j+1; continue
        j=i
        while j<n and s[j] not in ' \t\r\n()': j+=1
        yield s[i:j]; i=j
def parse(s):
    stack=[[]]
    for t in tokenize(s):
        if t=='(':
            stack.append([])
        elif t==')':
            x=stack.pop(); stack[-1].append(x)
        else: stack[-1].append(t)
    return stack[0]
def q(s): return '"'+str(s).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\t','\\t')+'"'
def dump(x,ind=0):
    if isinstance(x,list):
        parts=[dump(e,ind+1) for e in x]
        one='('+' '.join(parts)+')'
        if len(one)<100 and '\n' not in one: return one
        return '('+parts[0]+''.join('\n'+'  '*(ind+1)+p for p in parts[1:])+')'
    if isinstance(x,tuple): return q(x[1])
    return str(x)
def name(x): 
    v=x[1]; return v[1] if isinstance(v,tuple) else v
def find(x,key): return [e for e in x if isinstance(e,list) and e and e[0]==key]
