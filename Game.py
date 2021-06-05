"""
Create a game for RCSS.
"""
# imports
import threading
from Player_supervised_learning import Player

# ------------------------------------------------------------------------------
class Game:
    """
    """

    def __init__(self, team1, team2):
        """

        team1 - str: the name of team1
        team2 - str: the name of team2
        """

        self.team1 = self.create_team(team1)
        self.team2 = self.create_team(team2, True)

    def create_team(self, teamname, ki=False):
        """
        Create a team with 10 players and 1 goalie.

        Returns list of all players (list).

        teamname - str: the name of the team
        ki - bool: the flag to use the ki
        """

        # create team list
        team_list = list()

        # create and connect players for first team
        for i in range(10):
            # create new player
            new_player = Player(teamname, ki=ki)

            # add player to team list
            team_list.append(new_player)

            # run player in new thread
            new_thread = threading.Thread(target=new_player.run)
            new_thread.start()

            # write to console
            print('team {} player {} created'.format(teamname, i))

        # add goalie to team
        goalie = Player(teamname, True, ki)

        # add goalie to team list
        team_list.append(goalie)

        # run goalie in new thread
        new_thread = threading.Thread(target=goalie.run)
        new_thread.start()

        # write to console
        print('team {} goalie created'.format(teamname))

        return team_list

Game('Team1', 'Team2')


