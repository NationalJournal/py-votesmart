import os
import unittest

from votesmart import VoteSmartAPI
from votesmart.exceptions import VotesmartApiError


def _has_credentials():
    return (os.environ.get('VOTE_SMART_EMAIL')
            and os.environ.get('VOTE_SMART_PASSWORD'))


@unittest.skipIf(not _has_credentials(), 'no API credentials')
class LiveTestAPITestCase(unittest.TestCase):

    def setUp(self):
        self.vsmart = VoteSmartAPI(
            email=os.environ.get('VOTE_SMART_EMAIL'),
            password=os.environ.get('VOTE_SMART_PASSWORD'),
        )


class CandidatesTestCase(LiveTestAPITestCase):

    def test_getByOfficeState(self):
        results = self.vsmart.Candidates.getByOfficeState(3, 'NJ', electionYear=2009)
        self.assertGreater(len(results), 0)

    def test_getByLastname(self):
        results = self.vsmart.Candidates.getByLastname("Agris", electionYear="2012")
        self.assertGreater(len(results), 0)

    def test_getByElection(self):
        results = self.vsmart.Candidates.getByElection(3517)
        self.assertGreater(len(results), 0)

    def test_getByDistrict(self):
        results = self.vsmart.Candidates.getByDistrict(29538, electionYear=2012)
        self.assertGreater(len(results), 0)

    def test_getByZip(self):
        results = self.vsmart.Candidates.getByZip(92821, electionYear=2012)
        self.assertGreater(len(results), 0)


class DistrictTestCase(LiveTestAPITestCase):

    def test_getByZip(self):
        results = self.vsmart.District.getByZip(90001)
        self.assertGreater(len(results), 0)

    def test_getByOfficeState(self):
        results = self.vsmart.District.getByOfficeState(5, 'CA')
        self.assertGreater(len(results), 0)


class StateTestCase(LiveTestAPITestCase):

    def test_getStateIDs(self):
        results = self.vsmart.State.getStateIDs()
        self.assertGreater(len(results), 0)

    def test_getState(self):
        results = self.vsmart.State.getState('TX')
        self.assertEqual(results.name, "Texas")


class ElectionTestCase(LiveTestAPITestCase):

    def test_getElectionByYearState(self):
        results = self.vsmart.Election.getElectionByYearState(2010, 'TX')
        self.assertGreater(len(results), 0)

    def test_getElectionByZip(self):
        results = self.vsmart.Election.getElectionByZip('92821', year=2010)
        self.assertGreater(len(results), 0)

    def test_getStageCandidates(self):
        results = self.vsmart.Election.getStageCandidates('3217', 'G')
        self.assertGreater(len(results), 0)

    def test_getElection(self):
        results = self.vsmart.Election.getElection(3217)
        self.assertIsNotNone(results)


class OfficeTestCase(LiveTestAPITestCase):

    def test_getTypes(self):
        results = self.vsmart.Office.getTypes()
        self.assertGreater(len(results), 0)

    def test_getBranches(self):
        results = self.vsmart.Office.getBranches()
        self.assertGreater(len(results), 0)

    def test_getLevels(self):
        results = self.vsmart.Office.getLevels()
        self.assertGreater(len(results), 0)

    def test_getOfficesByLevel(self):
        results = self.vsmart.Office.getOfficesByLevel('F')
        self.assertGreater(len(results), 0)

    def test_getOfficesByType(self):
        results = self.vsmart.Office.getOfficesByType("L")
        self.assertGreater(len(results), 0)


class CandidateBioTestCase(LiveTestAPITestCase):

    def test_getBio(self):
        results = self.vsmart.CandidateBio.getBio(176111)
        self.assertIsNotNone(results)

    def test_getDetailedBio(self):
        results = self.vsmart.CandidateBio.getDetailedBio(176111)
        self.assertIsNotNone(results)


class RatingTestCase(LiveTestAPITestCase):

    def test_getCategories(self):
        results = self.vsmart.Rating.getCategories()
        self.assertGreater(len(results), 0)

    def test_getSigList(self):
        results = self.vsmart.Rating.getSigList("2")
        self.assertGreater(len(results), 0)

    def test_getSig(self):
        results = self.vsmart.Rating.getSig("331")
        self.assertIsNotNone(results)

    def test_getCandidateRating(self):
        results = self.vsmart.Rating.getCandidateRating(138524)
        self.assertGreater(len(results), 0)


class OfficialsTestCase(LiveTestAPITestCase):

    def test_getStatewide(self):
        results = self.vsmart.Officials.getStatewide(stateId='CA')
        self.assertGreater(len(results), 0)

    def test_getByOfficeState(self):
        results = self.vsmart.Officials.getByOfficeState('73', stateId='AL')
        self.assertGreater(len(results), 0)

    def test_getByLastname(self):
        results = self.vsmart.Officials.getByLastname("Battle")
        self.assertGreater(len(results), 0)

    def test_getByZip(self):
        results = self.vsmart.Officials.getByZip(90210)
        self.assertGreater(len(results), 0)


class NpatTestCase(LiveTestAPITestCase):

    def test_getNpat(self):
        results = self.vsmart.Npat.getNpat(176111)
        self.assertIsNotNone(results)


class MeasureTestCase(LiveTestAPITestCase):

    def test_getMeasuresByYearState(self):
        results = self.vsmart.Measure.getMeasuresByYearState(2016, 'CA')
        self.assertGreater(len(results), 0)

    def test_getMeasure(self):
        results = self.vsmart.Measure.getMeasure(2142)
        self.assertIsNotNone(results)


class LeadershipTestCase(LiveTestAPITestCase):

    def test_getPositions(self):
        results = self.vsmart.Leadership.getPositions()
        self.assertGreater(len(results), 0)

    def test_getOfficials(self):
        results = self.vsmart.Leadership.getOfficials(leadershipId=311)
        self.assertGreater(len(results), 0)


class LocalTestCase(LiveTestAPITestCase):

    def test_getCounties(self):
        results = self.vsmart.Local.getCounties('UT')
        self.assertGreater(len(results), 0)

    def test_getCities(self):
        results = self.vsmart.Local.getCities("UT")
        self.assertGreater(len(results), 0)

    def test_getOfficials(self):
        results = self.vsmart.Local.getOfficials(4018)
        self.assertGreater(len(results), 0)


class VotesTestCase(LiveTestAPITestCase):

    def test_getByBillNumber(self):
        results = self.vsmart.Votes.getByBillNumber("HB 1")
        self.assertGreater(len(results), 0)

    def test_getCategories(self):
        results = self.vsmart.Votes.getCategories(2024)
        self.assertGreater(len(results), 0)


class AddressTestCase(LiveTestAPITestCase):

    def test_getOfficeWebAddress(self):
        results = self.vsmart.Address.getOfficeWebAddress(138524)
        self.assertGreater(len(results), 0)

    def test_getOffice(self):
        results = self.vsmart.Address.getOffice(138524)
        self.assertGreater(len(results), 0)
