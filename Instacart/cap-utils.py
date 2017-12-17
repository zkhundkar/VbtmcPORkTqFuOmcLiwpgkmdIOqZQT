import numpy as np
import pandas as pd
import os
import time
import gc

print "Loaded numpy and pandas libraries"

_datapath = './'
os.chdir(_datapath)
RAW_STORE = 'instacart_raw.hdf5'
HDF_STORE = 'instacartU.hdf5'
FVARS_STORE = 'featuresU.hdf5'
STATS_STORE = 'stats.hdf5'
BASKETS = 'baskets.hdf5'
RANDOM_STATE = 46

def get_from_hdf(tnames, STORE=RAW_STORE):
    hnames = {}
    result = {}
    for n in tnames:
        name = hname[n] if n in hnames else n
        try:
            print "Loading {} datasets ...".format(n)
            result[n] = pd.read_hdf(STORE, name)
        except Exception as e:
            print e
            print "Dataset could not be loaded. Is the hdf store missing?"
    return result

def preprocess_orders(orders):

    orders.sort_values(by=['user_id', 'order_number'], inplace=True)

    # Add additional columns
    x = orders.days_since_prior_order
    orders['30plus_days'] = (x==30).astype('int8')

    # Impute 'missing' days_since_prior_order values
    orders.days_since_prior_order.fillna(orders.days_since_prior_order.mean(), inplace=True)
    ser=orders[x==30].index
    orders.days_since_prior_order[ser] = pd.DataFrame(np.random.randint(30,50,len(ser)), index=ser)
    orders['csum_ds'] = orders.groupby('user_id')['days_since_prior_order'].transform('cumsum') 

    # Transform
    orders['log_ds'] = np.log(orders.days_since_prior_order+1)

def get_hist_chunk(orders, priors, frac=0.05, seed=RANDOM_STATE, **kw):
    if 'start' in kw:
        start = kw['start']
        chunk = kw['size']
        ochunk = orders.iloc[start:start+chunk]
        print "Selected {} orders {}:{}.".format(len(ochunk), start, start+chunk)
    elif 'all' in kw:
        ochunk = orders
        print "Selected all orders."
    else:
        u = orders.groupby('user_id')['order_id'].last().reset_index()[['user_id']]
        u = u.sample(frac=frac, random_state=seed)
        ochunk = u.merge(orders, how="inner", on='user_id')
        print "Selected {} orders for {} users.".format(len(ochunk), len(u))
    ochunk.sort_values(by=['user_id', 'order_number'], inplace=True)
    p = ochunk.merge(priors, on='order_id')
    return p

def add_product_groups(p, products):
    return p.merge(products[['product_id', 'department_id', 'aisle_id']], on='product_id')

def diff_1(m):
    user = product = ""
    last = 0
    #print m.shape
    for row in m:
        if (user == row[0]) and (product == row[1]):
            save = row[3]
            row[3] -= last
            last = save
        else:
            user = row[0]
            product = row[1]
            last = row[3]

    return m

def user_product_ds_last(p):

        p2 = p[['user_id', 'product_id', 'order_number', 'csum_ds']]\
                .sort_values(by=['user_id', 'product_id', 'order_number'])
        g = pd.DataFrame(diff_1(p2.as_matrix()), dtype='int32')
        g.columns = ['user_id', 'product_id', 'order_number', 'ds_last']
        print len(g), g.columns 
        #p = p.merge(g, on=['user_id', 'product_id', 'order_number'])
        return g


def user_product_features(phist, verbosity=3):

    #phist = p[p.eval_set == 0]
    tic = tic0 = time.time()
    #order_count = phist.groupby(['user_id', 'order_id'])['.count().reset_index())
    if True: # inline comments
        up_feat = phist.groupby(['user_id', 'aisle_id', 'product_id'])\
                .agg({'reordered':['count', 'mean', 'last'], 'ds_last':'mean',\
                    'order_number':'max', 'add_to_cart_order':'mean'})\
                .reset_index()
        up_feat.columns=['user_id', 'aisle_id', 'product_id', 'up_cart_rank', 'up_avg_days',\
             'up_in_last', 'up_times', 'up_reord_prob', 'up_last_reord']
        up_feat['up_in_last'] = up_feat['up_in_last'].astype('int8')
        toc = time.time()
        if verbosity > 2:
            print "Step 1 / 4 - computed user-product averages {:.3f} s".format(toc - tic)
            tic = toc

        u_orders = phist.groupby(['user_id', 'order_id'])['product_id'].count().reset_index()
        u_orders = u_orders.groupby('user_id').agg({'order_id':'nunique', 'product_id':'mean'})\
                        .reset_index()
        u_orders.rename(columns={'order_id':'uo_count', 'product_id':'ubasket_avg'},\
                    inplace=True)
        up_feat = up_feat.merge(u_orders, on='user_id')
        up_feat["up_prob"] = up_feat.up_times / up_feat.uo_count
        del u_orders
        toc = time.time()
        if verbosity > 2:
            print "Step 2 / 4 - computed basket avg {:.3f} s".format(toc-tic)
            tic = toc

        ##TODO
        up_orders = phist.groupby(['user_id', 'product_id'])\
                    ['order_dow', 'order_hour_of_day', '30plus_days' ].mean()\
                    .reset_index()
        up_orders.rename(columns={'order_dow':'up_dow', 'order_hour_of_day':'up_tod',\
                     '30plus_days':'up_30_avg'}, inplace=True)
        up_feat = up_feat.merge(up_orders, on=['user_id', 'product_id'])
        del up_orders

        toc = time.time()
        if verbosity > 2:
            print "Step 3 / 4 - computed basket avg {:.3f} s".format(toc-tic)
            tic = toc

        pa_up = phist.groupby(['user_id', 'order_id', 'aisle_id'])\
            .agg({'product_id':'nunique',\
                'reordered':'sum'}).reset_index()
        pa_up.columns = ['user_id', 'order_id', 'aisle_id', 'u_a_pcount', 'u_a_reord']
        pa_up = pa_up.groupby(['user_id', 'aisle_id'])\
                .agg({'order_id':'count', 'u_a_pcount':'mean', 'u_a_reord':'mean'})\
                .reset_index()
        pa_up.rename(columns={'order_id':'ua_ocount'}, inplace=True)
        print pa_up.columns
        up_feat = up_feat.merge(pa_up, on=['user_id', 'aisle_id'])
        toc = time.time()
        if verbosity > 2:
            print "Step 4 / 4 {:.3f} s".format(toc - tic)
            tic = toc

        #pd_up = phist.groupby(['user_id', 'order_id', 'department_id'])\
        #    .agg({'product_id':'nunique', 'reordered':'mean'}).reset_index()
        #pd_up.columns = ['user_id', 'order_id', 'department_id', 'uo_dcount', 'uo_d_reord_prob']

        #a_p = phist.groupby(['aisle_id', 'product_id' ])\
        #            .agg({'order_id':'count', 'reordered':'mean'} ).reset_index()
        #a_p.columns = ['aisle_id', 'product_id', 'ap_freq', 'ap_reord_prob']
        #a_p.ap_freq = (a_p.ap_freq / a_p.ap_freq.max()).astype('float16')
        #up_feat = up_feat.merge(a_p, on=['aisle_id'])
    toc = time.time()
    if verbosity > -1:
        print "Completed in a total of {:.3f} s".format(toc - tic0)
        tic = toc
        print up_feat.columns
    return up_feat

def basket_features(phist, verbosity=3):
    tic = time.time()
    # Basket characteristics
    basket = phist.groupby(['user_id', 'order_id'])\
        .agg({'aisle_id':'nunique', 'department_id':'nunique',\
                     'product_id':'count', 'reordered':'mean'}).reset_index()
    basket.rename(columns={'aisle_id':'b_a_count', 'department_id':'b_d_count',\
                     'product_id':'b_pcount', 'reordered':'b_reord'}, inplace=True)

    basket_aisles = phist.groupby(['user_id', 'order_id', 'aisle_id'])['reordered']\
        .agg(['count', 'mean']).reset_index()
    basket_aisles.rename(columns={'count':'b_a_wt', 'mean':'b_a_reord'}, inplace=True)

    basket = basket_aisles.merge(basket, how='inner', on=['user_id', 'order_id'])

    toc = time.time()
    if verbosity > -1:
        print "Completed in a total of {:.3f} s".format(toc - tic)
        tic = toc

    #print a_p.describe()
    print basket.columns
    return basket

def get_sample(p, **kw):
    r"""
        requires two keyword inputs 
        by = column name
        frac = fraction of rows to sample
    """    
    try:
        colname = kw['by']
        frac = kw['frac'] if frac in kw else 0.05
        u = p[[colname]].unique()
        u = u.sample(frac=frac, random_state=seed)
        ochunk = p[p[[colname]].isin(u)]
    except NameError as e:
        ochunk = ""
        print e
    finally:
        del u
    print "Selected {}={:.2f}% rows of {} {}.".format(len(ochunk),\
            100.0*frac, int(len(u)*frac), colname)
    return ochunk

def later():
    ud_p=phist.groupby(['user_id', 'department_id', 'product_id' ])['reordered']\
        .agg(['count', 'mean'] ).reset_index()
    p_udp.columns = ['user_id', 'department_id', 'product_id', 'udp_count', 'udp_reord_prob']
    #print p_udp.describe()

    pa_up=phist.groupby(['user_id', 'order_id', 'aisle_id' ])\
        .agg({'product_id':'nunique',\
              'reordered':'mean'} ).reset_index()
    pa_up.columns = ['user_id', 'order_id', 'aisle_id', 'ua_pcount', 'ua_reord_prob']

    u_orders=u_orders.groupby('user_id').agg({'order_id':'nunique', 'product_id':'mean'})\
        .reset_index().rename(columns={'order_id':'uo_count', 'product_id':'ubasket_avg'})
    p_up=p_up.merge(u_orders, on='user_id')
    p_up['up_oprob'] = (p_up.up_total / p_up.uo_count).astype('float16')

    #print p_up.groupby(['user_id', 'product_id'])['up_total']drop('up_prob', axis=1, inplace=True)
    #u_order_count = len(p_up.up_total)
    #p_up['up_prob'] = p_up.up_total/u_order_count
    #order_count = len(p.groupby('order_id'))
    #pp_up= phist.groupby(['product_id'])['reordered'].agg(['count','mean','std']).reset_index()\
    #    .rename(columns={'count':'p_total', 'mean':'p_reord_prob', 'std':'p_reord_std'})    
    #pp_up['p_prob'] = (pp_up.p_total/order_count).astype('float16')
    #del pp
    #print order_count, len(pp_up[pp_up.p_total>1000])
    ##pd_up.columns=pd_up.columns.droplevel()
    #print a_p.describe()
    #print pp_up.describe()
    #print p_up.describe()
    #pp.reset_index(drop=True, inplace=True)
    #print priors[(priors.order_id==59336) ][['order_id','product_id','reordered']]
    #print orders[orders.user_id==59819][['user_id', 'order_id', 'order_number','eval_set']]
    #print pp.sort_values(by='count', ascending=False).head() 
    prod=19660
    user=59819
    oid=1079448
    #print p[(p.user_id==user) & (p.product_id==27966)].sort_values(by='order_number')[['order_number','eval_set','reordered']]
    #print p[p.order_id==oid]

    #orders=orders.sort_values(by=['user_id','order_number'])
    #o2=orders[orders.user_id==user].rename(columns={'days_since_prior_order':'ds'})
    #o2.ds=np.exp(o2.ds).astype('int8')
    ##o2['cum_ds']=o2.ds.cumsum()
    #print [0]+list(o2.cum_ds)[:-1]
    #o2['ds2']=[0]+list(o2.cum_ds)[:-1]
    #print o2[['ds', 'cum_ds', 'ds2']].head(10)
    

    #print o2[['user_id','order_number','ds','cum_ds','ds2']].head(10)
    #print p2.ds2
    #p2[p2.product_id==prod][['user_id','order_number','reordered','ds','cum_ds','ds2']].head(10)
    #p2.head()
    return

try:
    time.time()
except NameError:
    import time

NUM_AISLES = 134
CORR = np.zeros((NUM_AISLES+1)**2).reshape(NUM_AISLES+1, (NUM_AISLES+1))

def build_user_topn_aisles(p, topN=10):

    r"""
        Create dataframe with the top-N aisles a user shops in
        Input is a df from the priors table, with user_id and aisle_id
    """

    print "{} product ordered".format(len(p))
    gg = p.groupby(['user_id', 'order_id', 'aisle_id'])['product_id'].count().reset_index()
    print " ..  including products from {} aisles".format(len(gg))
    gg = gg.groupby(['user_id', 'aisle_id'])['product_id'].sum().reset_index()\
            .rename(columns={'product_id':'oa_count'})
    gg = gg.sort_values(by=['user_id', 'oa_count'], ascending=False)[['user_id', 'aisle_id']]
    gm = gg.groupby('user_id')['aisle_id'].unique().reset_index().as_matrix()
    print " .. {} users".format(gm.shape[0])

    dm = np.zeros((topN+1)*len(gm)).reshape(len(gm), topN+1)
    for i in xrange(len(gm)):
        dm[i] = np.concatenate([[gm[i][0]], gm[i][1], np.zeros(topN)])[:topN+1]
    g = pd.DataFrame(dm, dtype="int32")
    g.columns=['user_id']+['top-{}'.format(x) for x in range(1,topN+1)]

    return g

def add_aisles(a, corr=CORR):
    global NUM_AISLES
    X = np.zeros(NUM_AISLES+1).reshape(1, NUM_AISLES+1)
    for i in a:
        X[i] = 1
    for ip in a:
        corr[ip] += X
    return

def add_corr(x, corr):
    global NUM_AISLES
    user = ""
    order = ""
    user_count = 0
    user_aisles = []
    a_array = np.zeros(NUM_AISLES+1)
    u_array = np.zeros(NUM_AISLES+1)
    for row in x:
        if user == row[0] and order==row[1]:
            a_array[int(row[2])] = 1
        elif user==row[0]:
            u_array += a_array
            a_array = a_array*0
            row = row[1]
            a_array[int(row[2])] = 1
        else:
            if user:
                user_aisles.append(u_array)
                u_array = u_array*0
                a_array = a_array*0
            else:
                pass
            user_count += 1
            user = row[0]
            u_array[0] = user
            row = row[1]
            a_array[int(row[2])] = 1               

    return

def build_row(g, N=10):
    # g show be an array of aisle_ids
    # returns an array of the N-most frequent aisle_ids

    return row

def build_correlation(phist, **kw):
    csum = 0.0
    gsum = 0.0
    osum = 0
    chunk_size = kw['chunk_size'] if 'chunk_size' in kw else 20000
    max_iter = kw['max_iter'] if 'max_iter' in kw else 10
    ulist = phist[phist.eval_set<2].groupby(['user_id']).count().reset_index()
    chunk_size = min(chunk_size, len(ulist))

    #CORR = np.zeros((NUM_AISLES+1)).reshape(NUM_AISLES+1, (NUM_AISLES+1))

    if True:
        iter=c=0
        df=""
        r_range = xrange(0, len(ulist), chunk_size)
        for rowset in r_range:
            iter += 1
            start = rowset*chunk_size
            end = (rowset+1)*chunk_size
            oset = ulist.iloc[ulist.index[start:end]]
            c+= len(df)
            tic= time.time()
            g = oset[['user_id']].merge(phist, on=['user_id'])\
                .sort_values(by=['user_id', 'order_id'])
            add_corr(g[['user_id', 'order_id', 'aisle_id']].as_matrix(), CORR)
            osum += len(g)
            csum += time.time()-tic
            
            if iter % 4 == 0:
                print "{:2d} chunks in {:3f} s".format(iter, csum)
            if iter+1>max_iter:
                break

    #except Exception as e:
    #    print e

    #print "Count={}, orders={}, in {} iterations".format(c, osum, iter)
    #print "Processing took {} s".format(csum)

def corr_to_frame(corr):
    global NUM_AISLES

    cut = NUM_AISLES+1
    corr[0] = range(NUM_AISLES+1)
    c2 = corr[:cut].transpose()[:cut]
    c2 = pd.DataFrame(c2).astype('uint32')
    c2.rename(index=str, columns={0:'aisle_id'}, inplace=True)
    return c2

def topn_aisles(c2, topsort=15):
    global NUM_AISLES

    cut = NUM_AISLES+1
    zsorted=np.zeros(cut*(1+topsort)).reshape(cut, (1+topsort))
    
    for i in range(1,cut):
        sortcol=c2[c2.aisle_id !=i ].sort_values(by=i, ascending=False)
        zsorted[i]=np.concatenate([[i], list(sortcol[:topsort].index.astype('int8'))])

        #sortcol=c2[c2[0]!=i].sort_values(i, ascending=False)[:topsort]
        # sorted[i]=np.concatenate([[i], sortcol[0],  sortcol[i]/sortcol[i].sum()])
        #np.concatenate([[i], list(sortcol[:topsort].index.astype('int8')), np.array(sortcol[i]/sortcol[i].sum())[:topsort]])

    dd = pd.DataFrame(zsorted, dtype="int8").rename(columns=dict([(k+1, "top-{:d}".format(k+1)) for k in range(topsort)]))
    dd.rename(columns=dict([(k+topsort+1, "corr-{:d}".format(k+1)) for k in range(topsort)]), inplace=True)
    dd.rename(index=str, columns={0:'aisle_id'}, inplace=True)
    dd.aisle_id=dd.aisle_id.astype('int8')
    #for k in range(topsort):
    #    col='top-{}'.format(k+1)
    #    dd[col]=dd[col].astype('int')
    
    print dd[dd.aisle_id!=0].head()
    return dd
	
# --------- Beanhcmark models

# ---------- Benchmark 1 -- 
def bench1_fit(priors, orders):
    pset = orders[orders.eval_set==0][['order_id', 'user_id']]
    bench = priors.merge(pset,  on='order_id')

    # Calculate product popularity
    popular = bench[bench.reordered==1].groupby('product_id')['order_id'].count().reset_index()\
    .rename(columns={'order_id':'frequency'})
    popular.sort_values(by='frequency', ascending=False, inplace=True)

    #Calculate average basket size
    basket_size = bench.groupby('order_id')['product_id'].count()\
    .reset_index().rename(columns={'product_id':'Average Size'})
    topN = int(round(np.float(basket_size[[1]].mean()[0]), 0))
    print "Average basket size is {:.3f}".format(topN)
    
    model = popular.product_id[:topN].reset_index().drop('index', axis=1)
    model['in_order'] = (np.ones(len(model))).astype('uint8')
    return model

# ---------- Benchmark 2 -- 
def bench2_fit(priors, orders):
	# Add user_id to the historical set
	pset = orders[orders.eval_set==0][['order_id', 'user_id', 'order_number']]
	bench = priors.merge(pset,  on='order_id')
	model = bench.groupby(['user_id', 'product_id'])['order_number'].last().reset_index()
	model.rename(columns={'last':'in_order', 'order_number':'in_order'}, inplace=True)
	model.in_order = (model.in_order / model.in_order).astype('uint8')
	
	return model
	
# ---------- Benchmark 3 -- 
def bench3_fit(priors, orders):
	# Find the history set -- prior and train
	bench = orders[orders.eval_set==0][['order_id', 'user_id', 'order_number']]
	bench3 = bench.merge(priors, on='order_id')
	# Calculate most frequently purchased items by user
	popular = bench3.groupby(['user_id','product_id'])['order_id'].count().reset_index()\
				.rename(columns={'order_id':'frequency'})
	#popular.sort_values(by=['user_id', 'frequency'], ascending=[True, False], inplace=True)
	popular['prod_rank']=popular.groupby(['user_id'])['frequency']\
				.rank(ascending=False).astype('uint16')

	#Calculate average basket size
	u_baskets = bench3.groupby(['user_id', 'order_id'])['product_id'].count()\
		.reset_index().rename(columns={'product_id':'basket_size'})
	u_baskets = u_baskets.groupby('user_id')['basket_size'].mean().reset_index()
	model = popular.merge(u_baskets, on='user_id') 
	model['in_order'] = model.prod_rank[model.prod_rank<model.basket_size]
	return model[['user_id', 'product_id', 'in_order']]

# ---------- Benchmark predictions -- 

def	bench_predict(model, X):
	# Input X should be a dataframe including a user_id
	# Input model should be a dataframe with two or three columns:
	#		[user_id], product_id and in_order
	
	if 'user_id' in model.columns:
		X = X.merge(model[['user_id','product_id','in_order']], how='left', 
			on=['user_id', 'product_id'])
	else:
		X = X.merge(model, how='left', on='product_id')
	pred = X.in_order.fillna(0)
		
	return pred