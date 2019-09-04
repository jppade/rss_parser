from flask import Flask, render_template, request, escape
import read_rss as rr

app = Flask(__name__)
app.jinja_env.globals.update(zip=zip)


def log_request(req, res):
    with open('vsearch.log', 'a') as log:
        print(req.form,  file=log, end='|')
        print(req.remote_addr, file=log, end='\n' )
        #print(res, file=log, end='|')


@app.route('/search4', methods=['POST'])
def do_search():
    """Extract the posted data; perform the search; return results."""

    # Make a list of keywords from the entered string containing several words.
    words_raw = request.form['words']
    words = [word.strip() for word in words_raw.split(',')]

    # Retreive threshold value
    try:
        threshold = int(request.form['threshold'])
        errorstring = ''
    except ValueError:
        # When the visualization checkbox is still checked, we draw the graph
        # with a default value threshold=20.
        errorstring = "You did not enter an integer for the threshold value,"\
                    "hence we set it to its default value 20. "
        threshold = False

    # Retreive visualization value
    try:
        visualization = request.form['visualization']
    except KeyError:
        visualization = False

    # Run code for feed suggestions (backend)
    results, title_list = rr.article_suggestion(words)
    num_results = len(results)

    # Plot interaction graph if box is checked and get eigenvector centrality
    if visualization and threshold:
        rr.interaction_graph(threshold, show=False)
        lst_sorted = rr.eigenvector_centrality(threshold)
    elif visualization and not threshold:
        rr.interaction_graph(20, show=False)
        lst_sorted = rr.eigenvector_centrality(20)
    else:
        lst_sorted = rr.eigenvector_centrality(20)
    words_ordered = lst_sorted[0]

    # Transfer results to the results page
    log_request(request, results)
    return render_template('results.html',
                           the_words=', '.join(words),
                           the_threshold=threshold,
                           errorstring=errorstring,
                           the_results=results,
                           num_results=num_results,
                           visualization=visualization,
                           title_list=title_list,
                           words_ordered=words_ordered,)


# the entry_page method
@app.route ('/')
@app.route('/entry')
def entry_page() ->'html':
    return render_template('entry.html', 
                           the_title='Welcome to the newsfeed search engine!')


@app.route('/description')
def description_page():
    return render_template('description.html')


@app.route('/viewlog')
def view_log() ->str:
    with open('vsearch.log') as log:
        contents = log.read()
    return escape(''.join(contents))


if __name__=='__main__':

    app.run(debug=True)
