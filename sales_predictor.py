'''Sales Predictor'''
import csv
from collections import defaultdict
from datetime import datetime
import io
import pandas as pd


def get_month_on_month_sales(filepath):
    '''
    This function opens and reads the csv file. It reads through each row and
    extracts the infomation and records the data of the sales per month and the
    quantity of the beers ordered each month.
    '''
    with open(filepath, 'r', newline='') as f:
        d_i = defaultdict(int)
        cvsreader = csv.reader(f, delimiter=',')
        row_number = 0
        for row in cvsreader:
            if row_number != 0:
                dte = datetime.strptime(row[2], "%d-%b-%y")
                month = datetime(dte.year, dte.month, 1).strftime("%b")
                d_i[(dte.year, month)] += int(row[5])
            row_number += 1

        # init month on month sales data into table
        d = {'Month': [], 'Quant': []}

        # extract months
        k = d_i.keys()
        k = [x for x in k]
        k = [k[i][1] for i in range(12)]

        # extract corresponding monthly sales
        v = d_i.values()
        v = [x for x in v]
        v = [v[i] for i in range(12)]

        # setup month on month sales data table
        d['Month'] = k
        d['Quant'] = v

        return d

def get_predicted_sales(filepath, o_p='html'):
    '''
    This function uses the data which is provided from the reading of the csv file
    to predict the sales of the beer, individually and the total sales prediciton
    per month to provide a prediciton for the sales across the upcoming months.
    '''
    # extract average percentage sales growth month-in-month from past sales data
    if not filepath:
        return None, None, None

    mom_sales_data = get_month_on_month_sales(filepath)
    df = pd.DataFrame.from_dict(mom_sales_data)
    df.reset_index(inplace=True)
    df.set_index("Month", inplace=True)
    growth_rate = df.pct_change().describe()['Quant'][1]

    # extract individual beer quantities and the total sold from past sales data
    df1 = pd.read_csv('Barnabys_sales_fabricated_data.csv')
    dunkel = df1.loc[lambda df1: df1['Recipe'] == 'Organic Dunkel', :].sum()['Quantity ordered']
    red_helles = df1.loc[lambda df1: df1['Recipe'] == 'Organic Red Helles', :].sum()['Quantity ordered']
    pilsner = df1.loc[lambda df1: df1['Recipe'] == 'Organic Pilsner', :].sum()['Quantity ordered']
    total_order = df1.sum()['Quantity ordered']

    # construct predicted sales table based percentage sales growth
    # over past year and ratios of individual beers sold
    predicted_sales = {'Dunkel': [],
                       'Red Helles' : [],
                       'Pilsner' : [],
                       'Total' : []
                      }
    for x in range(12):
        mon = mom_sales_data['Month'][x]
        mon_order = round((growth_rate * mom_sales_data['Quant'][x]) + mom_sales_data['Quant'][x])
        mon_dunkel = round(mon_order * (dunkel/total_order))
        mon_red_helles = round(mon_order * (red_helles/total_order))
        mon_pilsner = round(mon_order * (pilsner/total_order))
        predicted_sales['Total'].append(mon_order)
        predicted_sales['Dunkel'].append(mon_dunkel)
        predicted_sales['Red Helles'].append(mon_red_helles)
        predicted_sales['Pilsner'].append(mon_pilsner)


    # construct predicted sales dataframe to build HTML and/or CSV output
    df2 = pd.DataFrame.from_dict(predicted_sales)
    df2['Month'] = pd.date_range('11/01/2019', periods=12, freq='M')

    if o_p == 'csv':
        df2.to_csv('static\predicted_sales.csv', sep=',')

    if o_p == 'html':
        df2.to_html('templates\predicted_sales.html')

    # get an HTML table in string format of predicted sales suitable
    # for rendering using the flash framework
    str_io = io.StringIO()
    mstr = df2.to_html(buf=str_io, classes='table table-striped')
    html_str = str_io.getvalue()
    #print(html_str)

    return mom_sales_data, df2, html_str

def test_get_predicted_sales():
    '''
    Unit test
    '''
    mom_sales_data, df2, html_str = get_predicted_sales('')
    mom_sales_data, df2, html_str = get_predicted_sales('Barnabys_sales_fabricated_data.csv', 'csv')
    mom_sales_data, df2, html_str = get_predicted_sales('Barnabys_sales_fabricated_data.csv', 'html')
    mom_sales_data, df2, html_str = get_predicted_sales('Barnabys_sales_fabricated_data.csv', 'sap')
    return


if __name__ == "__main__":
    # unit tests
    test_get_predicted_sales()
