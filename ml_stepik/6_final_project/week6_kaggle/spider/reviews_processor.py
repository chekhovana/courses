import pandas as pd

fname_txt = 'data/reviews.txt'
fname_csv = 'data/reviews.csv'


def convert_reviews():
    df = pd.read_csv(fname_txt, header=None, sep='\t', names=['link', 'rating', 'review'])
    df['label'] = (df['rating'] > 3).astype(int)
    df.to_csv(fname_csv, columns=['label', 'review'], index=False, sep='\t')


convert_reviews()
