import re

ent_pattern = re.compile(r'(T\d+)\t([^\t]+) ((?:\d+ \d+;)*\d+ \d+)\t(.+)')
event_pattern = re.compile(r'(E\d+)\t([^\t:]+):(T\d+)(\s+(([^\t:]+):(T\d+))+)?')
rel_pattern = re.compile(r'R\d+\t(\S+) Arg1:(T\d+) Arg2:(T\d+)')
equiv_pattern = re.compile(r'\*\tEquiv ((?:T\d+[\s])+)')
attrib_pattern = re.compile(r'A\d+\t(\S+) ((?:[TE]\d+[\s])+)')
norm_pattern = re.compile(r'N\d+\tReference (T\d+) ((?:[^:])+):((?:[^\t])+)\t.+')
