import feedparser as fp
from collections import Counter
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import re
import string

excluded_words_path = './static/excluded_words.txt'
feedlist_path = './static/rss_list.txt'


def naked_word(strng):
    """ Deletes all punctuations at the beginning and the end of a string.
    Furthermore, delete newline command \n if in the middle of a string.
    Remark: This could also be done using regular expressions.
    However, it doesn't seem to be faster with regexs. And it's not obvious
    how to handle special cases such as 'a 60-metre tall semi-circle'."""
    if "\n" in strng:
        lst = strng.split("\n")
        strng = ''.join(lst)
    special_chars = ["'s", "’s", ".&nbsp"]
    strng = strng.rstrip()
    if strng:
        # Check start of string
        while strng[0] in string.punctuation:
            if strng in string.punctuation:
                ## String is only a punctuation
                return
            else:
                strng = strng[1:]
        # check end of string
        while strng[-1] in string.punctuation:
            if strng in string.punctuation:
                return
            else:
                strng = strng[:-1]
        for ending in special_chars:
            if ending in strng:
                strng = strng.split(ending)[0]
    return strng
    
    

def count_words(strng, excluded_words=''):
    """ Counts words in a string and returns their frequency in a dictionary.
    In case excluded_words is the name of an existing text file, the words
    from this file are excluded in the count."""
    
    # Unify notation
    id_dict = {'trump': {'donald trump', 'president trump',
                         'president donald trump'},
               'merkel': {'angela merkel', 'chancellor merkel',
                          'chancellor angela merkel'},
               'usa': {'u.s.', 'US', 'U.S.', 'united states',
                       'united states of america'}}
    wordFreq = dict()
    strng = strng.lower()
    for key in id_dict.keys():
        for value in id_dict[key]:
            strng = strng.replace(value, key)

    # count words
    line = strng.split(' ')
    if excluded_words:
        # In this case, there is a list of excluded words which should not
        # be included in the word count.
        # Import excluded words as a list
        excluded_list = list()
        with open(excluded_words) as fl:
            for excl_word in fl:
                excluded_list.append(naked_word(excl_word))
        # Make dictionary of word frequencies
        for word in line:
            word = naked_word(word)
            if word:
                # Now count words. If word is in excluded list continue
                # without doing anything.
                if word.lower() in excluded_list:
                    continue
                else:
                    wordFreq.setdefault(word.lower(), 0)
                    wordFreq[word.lower()] += 1
    else:
        for word in line:
            word = naked_word(word)
            if word:
                # Unify spelling of US
                wordFreq.setdefault(word.lower(), 0)
                wordFreq[word.lower()] += 1

    return wordFreq


def update_dict(current_dict, url, fld='summary', thrshld=False, excluded_words=''):
    """ Updates a dictionary which collects word frequencies with words given
    by an RSS-feed given by @url.
    @fld is usually chosen as 'title' or 'summary'.
    @thrshld can be chosen as integer. In this case, only words with frequency
            above thrshld are returned. By default, threshold is not set.
    @excluded_words can be a file name, words contained in this file are
    deleted in the returned dictionary. By default, none are deleted."""
    d = fp.parse(url)
    for feed in d.entries:
        if fld in feed.keys():
            # Remove html ---
            clean_feed = re.sub('<.*?>', '', feed[fld])
            # Update word count
            if thrshld:
                current_dict = dict(Counter(current_dict)
                                + Counter(count_words(clean_feed, excluded_words=excluded_words)))
                current_dict = dict({item for item in current_dict.items()
                if int(item[1] > thrshld)})
            else:
                current_dict = dict(Counter(current_dict)
                                + Counter(count_words(clean_feed, excluded_words=excluded_words)))
    return current_dict


def top_words(lst=feedlist_path, field='summary', excluded_words=excluded_words_path, threshold=4):
    """Return the top used words from a list of rss-feeds, excluding a list
    of words given in the text file excl_words.
    @field argument see update_dict.
    Only words which have a count above threshold are returned."""
    word_freqs = dict()
    with open(lst) as file:
        for url in file:
            # word_freqs = update_dict(word_freqs, url, fld=field)
            word_freqs = update_dict(word_freqs, url, fld=field,
                                     excluded_words=excluded_words)
    sorted_dict = sorted(word_freqs.items(), key=lambda x: x[1], reverse=True)
    return [tup for tup in sorted_dict if tup[1] > threshold]


def dict2adjacencycoarse(thr, feedlist=feedlist_path, field='summary', excluded_words=excluded_words_path):
    """ Returns an adjacency matrix the nodes of which correspond to the words
    in the list. The entry (i,j) counts the number of times that word i and j
    appear in the same summary.Furthermore, a list of words from the feedlist
    with frequency greater than @thr is returned. Each list entry is a tupel
    consisting of the word and its frequency.
    Words from the file given in @excluded_words are excluded.
    In contrast to dict2adjacency all newsfeeds from an rss feed are
    included in the adjacency matrix."""

    # Complete list of buzzwords with corresponding empty adacency matrix
    complete_list = top_words(lst=feedlist, field=field, excluded_words=excluded_words, threshold=thr)
    adjacency = np.zeros((len(complete_list),) * 2)

    # A list where each entry is a dictionary with the most frequent words
    # from one rss-feed.
    word_freqs = list()
    with open(feedlist) as file:
        for url in file:
            word_freqs.append(update_dict([], url, fld=field))

    for i in range(len(complete_list)):
        for k in range(i, len(complete_list)):
            for feed in word_freqs:
                if complete_list[i][0] in feed and complete_list[k][0] in feed:
                    adjacency[i, k] += 1
                    adjacency[k, i] += 1

    return adjacency, complete_list


def dict2adjacency(thr, feedlist=feedlist_path, field='summary', excluded_words=excluded_words_path):
    """ Returns an adjacency matrix the nodes of which
    correspond to the words in the list. Furthermore, a list of words from
    the feedlist with frequency greater than THR is returned. Each list entry
    is a tupel consisting of the word and its frequency. The entry (i,j)
    counts the number of times that word i and j appear in the same summary.
    Words from the file given in EXCLUDED_WORDS are excluded."""

    # Complete list of buzzwords with corresponding empty adacency matrix
    complete_list = top_words(lst=feedlist, field=field,
                              excluded_words=excluded_words, threshold=thr)
    adjacency = np.zeros((len(complete_list),) * 2)

    with open(feedlist) as file:
        for url in file:
            d = fp.parse(url)
            for feed in d.entries:
                if field in feed.keys():
                    clean_feed = feed[field].split("<")[0]
                    words_feed = count_words(clean_feed)
                    if words_feed:
                        for i in range(len(complete_list)):
                            for k in range(i, len(complete_list)):
                                if complete_list[i][0] in words_feed and complete_list[k][0] in words_feed:
                                    adjacency[i, k] += min(words_feed[complete_list[i][0]], words_feed[complete_list[k][0]])
                                    adjacency[k, i] = adjacency[i, k]

    return adjacency, complete_list


def interaction_graph(threshold, excluded_words=excluded_words_path, show=True):
    """ A (weighted) graph is plotted in the following manner: The nodes are
    the most frequent words above @threshold. Words from the file given in
    @excluded_words are excluded. """

    # Get adjacency matrix along with a list of the most frequent words ---
    adjacency, top_list = dict2adjacency(threshold, feedlist=feedlist_path, field='summary',
                                         excluded_words=excluded_words)

    # Circular layout ---
    num_nodes = adjacency.shape[0]
    positions = [(np.real(np.exp(2*np.pi*1j*k/num_nodes)), np.imag(np.exp(2*np.pi*1j*k/num_nodes)))
                 for k in range(num_nodes)]

    # Define the positions and labels of nodes and edge's weights and labels---
    plt.figure(num=None, figsize=(14, 10))
    G = nx.Graph()
    for i in range(num_nodes):
        G.add_node(i, pos=positions[i])
        for k in range(i, num_nodes):
            if adjacency[i, k] > 0:
                G.add_edge(i, k, weight=adjacency[i, k])

    pos = nx.get_node_attributes(G, 'pos')
    labels = nx.get_edge_attributes(G, 'weight')
    labeldict = dict({(i, top_list[i]) for i in range(num_nodes)})
    edges = G.edges()
    weights = [G[u][v]['weight']/2 for u, v in edges]

    # Begin plotting ----
    nx.draw_networkx_labels(G, pos, labels=labeldict, font_size=14, font_weight='bold')
    nx.draw_networkx_nodes(G, pos, node_color='pink')
    nx.draw_networkx_edges(G, pos, edges=edges, width=weights, alpha=0.4)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, font_color='red')

    title_font = {'style': 'oblique', 'family': 'serif', 'weight': 'normal', 'size': 18}
    plt.title("Relations between most frequent words.", fontdict=title_font)
    plt.axis('off')

    if show:
        plt.show()
    else:
        plt.savefig('./static/images/interaction_graph.png', format='png')
    return adjacency, top_list


def article_suggestion(words, lst=feedlist_path, field='summary'):
    """ For a given list of words an article from a list of rss-feeds
    is suggested. Depending on the @field variable, the words are either
    contained in the title or in the summary of the article. The links
    are sorted in descending order of the found word frequency. """
    article_dict = dict()
    title_list = list()
    with open(lst) as file:
        for url in file:
            d = fp.parse(url)
            for feed in d.entries:
                if field in feed.keys():
                    # Delete html ---
                    clean_feed = feed[field].split("<")[0]
                    words_feed = count_words(clean_feed)
                    if 'US' in words or 'IS' in words:
                        # Special treatment of these two capital-lettered words.
                        pass
                    else:
                        if all([word.lower() in words_feed for word in words]):
                            article_dict[feed['link']] = sum([words_feed[word] for word in words])
                            title_list.append(feed['title'])

    sorted_articles = sorted(article_dict.items(), key=lambda x: x[1])
    link_list = [item[0] for item in sorted_articles]
    return link_list, title_list


def eigenvector_centrality(thr, feedlist=feedlist_path, field='summary', excluded_words=excluded_words_path):
    """Compute the eigenvector centrality of the nodes of the graph obtained
    from dict2adjacency(*args)."""
    adj, toplist = dict2adjacency(thr, feedlist=feedlist, field=field, excluded_words=excluded_words)
    w, v = np.linalg.eig(adj)
    # Get the eigenvector corresponding to the largest eigenvalue (in case
    # python chooses the eigenvector to have all negative entries change
    # the sign).
    eigenvector = v[:, 0]
    if any([entry < 0 for entry in eigenvector]):
        eigenvector = -eigenvector/w[0]
    toplist_keys = [name[0] for name in toplist]
    toplist_sorted = [x for _,x in sorted(zip(eigenvector, toplist_keys), reverse=True)]
    return toplist_sorted, sorted(eigenvector, reverse=True)