""" recommendations """
from collections import Counter
from datetime import datetime

from dateutil.parser import parse as parse_date

from utils.config import BLOB_SIZE
from utils.human_ids import dehumanize
from utils.test_utils import API_URL, req, req_with_auth

RECOMMENDATION_URL = API_URL + '/recommendations'


def check_recos(recos):
    # ensure we have no duplicate mediations
    ids = list(filter(lambda id: id != None,
                      map(lambda reco: reco['mediationId'],
                          recos)))
    assert len(list(filter(lambda v: v>1, Counter(ids).values()))) == 0

    # ensure we have no mediations for which all stocks are past their bookingLimitDatetime
    for reco in recos:
        if 'mediation' in reco\
           and 'tutoIndex' not in reco['mediation']:
            assert not all([stock['bookingLimitDatetime'] is not None and
                            parse_date(stock['bookingLimitDatetime']) <= datetime.utcnow()
                            for stock in oc['stocks'] for oc in reco['mediatedOccurrences']])
            if not reco['event']['isNational']:
                assert not all([oc['venue']['departementCode'] != '93' for oc in reco['mediatedOccurrences']])


def subtest_initial_recos():
    r = req_with_auth().put(RECOMMENDATION_URL, json={'seenOfferIds': []})
    assert r.status_code == 200
    recos = r.json()
    assert len(recos) == 48

    assert recos[0]['mediation']['tutoIndex'] == 0
    assert recos[1]['mediation']['tutoIndex'] == 1

    assert len(list(filter(lambda reco: 'mediation' in reco and
                                        reco['mediation']['tutoIndex'] is not None,
                           recos))) == 2

    check_recos(recos)
    return recos


def subtest_recos_with_params(params,
                              expected_status=200,
                              expected_mediation_id=None,
                              expected_offer_id=None,
                              is_tuto=False):
    r = req_with_auth().put(RECOMMENDATION_URL+'?'+params, json={})
    assert r.status_code == expected_status
    if expected_status == 200:
        recos = r.json()
        assert len(recos) <= BLOB_SIZE + (2 if expected_mediation_id is None
                                            else 3)
        assert len(list(filter(lambda reco: 'mediation' in reco and
                                            reco['mediation']['tutoIndex'] is not None,
                               recos))) == (1 if is_tuto else 0)
        if expected_mediation_id:
            assert recos[0]['mediationId'] == expected_mediation_id
        if expected_offer_id:
            assert recos[0]['offerId'] == expected_offer_id
        check_recos(recos)
        return recos


def test_10_put_recommendations_should_work_only_when_logged_in():
    r = req.put(RECOMMENDATION_URL)
    assert r.status_code == 401


def test_11_put_recommendations_should_return_a_list_of_recos():
    recos1 = subtest_initial_recos()
    assert len(list(filter(lambda reco: 'mediationId' in reco and
                                        'offerId' in reco,
                           recos1))) > 0
    recos2 = subtest_initial_recos()
    assert len(recos1) == len(recos2)
    assert any([recos1[i]['id'] != recos2[i]['id']
                for i in range(2, len(recos1))])


def test_12_if_i_request_a_specific_reco_it_should_be_first():
    # Full request
    subtest_recos_with_params('offerId=AFQA&mediationId=AM',  # AM=1 AFQA=352
                              expected_status=200,
                              expected_mediation_id='AM',
                              expected_offer_id='AFQA')
    # No mediationId but offerId
    subtest_recos_with_params('offerId=AFQA',
                              expected_status=200,
                              expected_mediation_id='AM',
                              expected_offer_id='AFQA')
    # No offerId but mediationId
    subtest_recos_with_params('mediationId=AM',
                              expected_status=200,
                              expected_mediation_id='AM',
                              expected_offer_id='AFQA')


def test_13_requesting_a_reco_with_bad_params_should_return_404():
    # offerId correct and mediationId correct but not the same event
    subtest_recos_with_params('offerId=AQ&mediationId=AE',
                              expected_status=404)
    # invalid (not matching an object) offerId with valid mediationId
    subtest_recos_with_params('offerId=ABCDE&mediationId=AM',
                              expected_status=404)
    # invalid (not matching an object) mediationId with valid offerId
    subtest_recos_with_params('offerId=AE&mediationId=ABCDE',
                              expected_status=404)
    # invalid (not matching an object) mediationId with invalid (not matching an object) offerId
    subtest_recos_with_params('offerId=ABCDE&mediationId=ABCDE',
                              expected_status=404)


def test_14_actual_errors_should_generate_a_400():
    pass
    #TODO
    # invalid (not dehumanizable) offerId with valid mediationId
    # subtest_recos_with_params('offerId=00&mediationId=AE',
    #                          expected_status=400)
    # invalid (not dehumanizable) mediationId with valid offerId
    #subtest_recos_with_params('offerId=AE&mediationId=00',
    #                          expected_status=400)
    # invalid (not dehumanizable) mediationId with invalid (not dehumanizable) offerId
    #subtest_recos_with_params('offerId=00&mediationId=00',
    #                          expected_status=400)


#def test_15_if_i_request_a_specific_reco_with_singleReco_it_should_be_single():
#    r = req_with_auth().put(RECOMMENDATION_URL+'?offerType=event&offerId=AE&singleReco=true', json={})
#    assert r.status_code == 200
#    recos = r.json()
#    assert len(recos) == 1
#    assert recos[0]['mediation']['eventId'] == 'AE'


def test_16_once_marked_as_read_tutos_should_not_come_back():
    r = req_with_auth().put(RECOMMENDATION_URL, json={})
    assert r.status_code == 200
    recos_before = r.json()
    assert recos_before[0]['mediation']['tutoIndex'] == 0
    assert recos_before[1]['mediation']['tutoIndex'] == 1
    r_update = req_with_auth().patch(API_URL + '/recommendations/' + recos_before[0]['id'],
                                     json={'dateRead': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')})
    assert r_update.status_code == 200

    r = req_with_auth().put(RECOMMENDATION_URL, json={})
    assert r.status_code == 200
    recos_after = r.json()
    assert recos_after[0]['mediation']['tutoIndex'] == 1
    assert 'mediation' not in recos_after[1]\
           or recos_after[1]['mediation']['tutoIndex'] is None


def test_17_put_recommendations_should_return_more_recos():
    r = req_with_auth().put(RECOMMENDATION_URL, json={})
    assert r.status_code == 200
    recos = r.json()
    # ensure we still have no duplicates
    ids = list(map(lambda reco: reco['id'], recos))
    assert len(list(filter(lambda v: v > 1, Counter(ids).values()))) == 0


def test_18_patch_recommendations_should_return_is_clicked_true():
    r = req_with_auth().put(RECOMMENDATION_URL, json={})
    assert r.status_code == 200
    recos = r.json()
    recoId = recos[0]['id']
    r_update = req_with_auth().patch(API_URL + '/recommendations/' + recoId,
                                     json={'isClicked': True})
    assert r_update.status_code == 200
    assert r_update.json()['isClicked']


def test_19_put_recommendations_should_not_return_already_seen_recos():
    r = req_with_auth().put(RECOMMENDATION_URL, json={})
    assert r.status_code == 200
    recos_before = r.json()
    seen_recommendations = recos_before[:20]
    seen_recommendations_ids = list(map(lambda x: x['id'], seen_recommendations))

    r = req_with_auth().put(RECOMMENDATION_URL, json={'seenRecommendationIds': seen_recommendations_ids})
    assert r.status_code == 200
    recos_after = r.json()
    recos_after_id = [reco['id'] for reco in recos_after]

    intersection_between_seen_and_recommended = set(seen_recommendations_ids).intersection(set(recos_after_id))
    assert len(intersection_between_seen_and_recommended) == 0

