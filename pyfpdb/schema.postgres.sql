
DROP TABLE IF EXISTS Settings CASCADE;
CREATE TABLE Settings (version SMALLINT);

DROP TABLE IF EXISTS Sites CASCADE;
CREATE TABLE Sites (
		id SERIAL UNIQUE, PRIMARY KEY (id),
		name varchar(32),
		currency char(3));

DROP TABLE IF EXISTS Gametypes CASCADE;
CREATE TABLE Gametypes (
		id SERIAL UNIQUE, PRIMARY KEY (id),
		siteId INTEGER, FOREIGN KEY (siteId) REFERENCES Sites(id),
		type char(4),
		base char(4),
		category varchar(9),
		limitType char(2),
		hiLo char(1),
		smallBlind int,
		bigBlind int,
		smallBet int,
		bigBet int);

DROP TABLE IF EXISTS Players CASCADE;
CREATE TABLE Players (
		id SERIAL UNIQUE, PRIMARY KEY (id),
		name VARCHAR(32),
		siteId INTEGER, FOREIGN KEY (siteId) REFERENCES Sites(id),
		comment text,
		commentTs timestamp without time zone);

DROP TABLE IF EXISTS Autorates CASCADE;
CREATE TABLE Autorates (
		id BIGSERIAL UNIQUE, PRIMARY KEY (id),
		playerId INT, FOREIGN KEY (playerId) REFERENCES Players(id),
		gametypeId INT, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
		description varchar(50),
		shortDesc char(8),
		ratingTime timestamp without time zone,
		handCount int);

DROP TABLE IF EXISTS Hands CASCADE;
CREATE TABLE Hands (
		id BIGSERIAL UNIQUE, PRIMARY KEY (id),
		tableName VARCHAR(20),
		siteHandNo BIGINT,
		gametypeId INT, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
		handStart timestamp without time zone,
		importTime timestamp without time zone,
		seats SMALLINT,
		maxSeats SMALLINT,
		comment TEXT,
		commentTs timestamp without time zone);

DROP TABLE IF EXISTS BoardCards CASCADE;
CREATE TABLE BoardCards (
		id BIGSERIAL UNIQUE, PRIMARY KEY (id),
		handId BIGINT, FOREIGN KEY (handId) REFERENCES Hands(id),
		card1Value smallint,
		card1Suit char(1),
		card2Value smallint,
		card2Suit char(1),
		card3Value smallint,
		card3Suit char(1),
		card4Value smallint,
		card4Suit char(1),
		card5Value smallint,
		card5Suit char(1));

DROP TABLE IF EXISTS TourneyTypes CASCADE;
CREATE TABLE TourneyTypes (
		id SERIAL, PRIMARY KEY (id),
		siteId INT, FOREIGN KEY (siteId) REFERENCES Sites(id),
		buyin INT,
		fee INT,
		knockout INT,
		rebuyOrAddon BOOLEAN);

DROP TABLE IF EXISTS Tourneys CASCADE;
CREATE TABLE Tourneys (
		id SERIAL UNIQUE, PRIMARY KEY (id),
		tourneyTypeId INT, FOREIGN KEY (tourneyTypeId) REFERENCES TourneyTypes(id),
		siteTourneyNo BIGINT,
		entries INT,
		prizepool INT,
		startTime timestamp without time zone,
		comment TEXT,
		commentTs timestamp without time zone);

DROP TABLE IF EXISTS TourneysPlayers CASCADE;
CREATE TABLE TourneysPlayers (
		id BIGSERIAL UNIQUE, PRIMARY KEY (id),
		tourneyId INT, FOREIGN KEY (tourneyId) REFERENCES Tourneys(id),
		playerId INT, FOREIGN KEY (playerId) REFERENCES Players(id),
		payinAmount INT,
		rank INT,
		winnings INT,
		comment TEXT,
		commentTs timestamp without time zone);

DROP TABLE IF EXISTS HandsPlayers CASCADE;
CREATE TABLE HandsPlayers (
		id BIGSERIAL UNIQUE, PRIMARY KEY (id),
		handId BIGINT, FOREIGN KEY (handId) REFERENCES Hands(id),
		playerId INT, FOREIGN KEY (playerId) REFERENCES Players(id),
		startCash INT,
		position CHAR(1),
		seatNo SMALLINT,
		ante INT,
	
		card1Value smallint,
		card1Suit char(1),
		card2Value smallint,
		card2Suit char(1),
		card3Value smallint,
		card3Suit char(1),
		card4Value smallint,
		card4Suit char(1),
		card5Value smallint,
		card5Suit char(1),
		card6Value smallint,
		card6Suit char(1),
		card7Value smallint,
		card7Suit char(1),
	
		winnings int,
		rake int,
		comment text,
		commentTs timestamp without time zone,
		tourneysPlayersId BIGINT, FOREIGN KEY (tourneysPlayersId) REFERENCES TourneysPlayers(id));

DROP TABLE IF EXISTS HandsActions CASCADE;
CREATE TABLE HandsActions (
		id BIGSERIAL UNIQUE, PRIMARY KEY (id),
		handPlayerId BIGINT, FOREIGN KEY (handPlayerId) REFERENCES HandsPlayers(id),
		street SMALLINT,
		actionNo SMALLINT,
		action CHAR(5),
		amount INT,
		comment TEXT,
		commentTs timestamp without time zone);

DROP TABLE IF EXISTS HudCache CASCADE;
CREATE TABLE HudCache (
		id BIGSERIAL UNIQUE, PRIMARY KEY (id),
		gametypeId INT, FOREIGN KEY (gametypeId) REFERENCES Gametypes(id),
		playerId INT, FOREIGN KEY (playerId) REFERENCES Players(id),
		activeSeats SMALLINT,
		position CHAR(1),
		tourneyTypeId INT, FOREIGN KEY (tourneyTypeId) REFERENCES TourneyTypes(id),
		
		HDs INT,
		street0VPI INT,
		street0Aggr INT,
		street0_3B4BChance INT,
		street0_3B4BDone INT,
		street1Seen INT,
		street2Seen INT,
		street3Seen INT,
		street4Seen INT,
		sawShowdown INT,
		street1Aggr INT,
		street2Aggr INT,
		street3Aggr INT,
		street4Aggr INT,
		otherRaisedStreet1 INT,
		otherRaisedStreet2 INT,
		otherRaisedStreet3 INT,
		otherRaisedStreet4 INT,
		foldToOtherRaisedStreet1 INT,
		foldToOtherRaisedStreet2 INT,
		foldToOtherRaisedStreet3 INT,
		foldToOtherRaisedStreet4 INT,
		wonWhenSeenStreet1 FLOAT,
		wonAtSD FLOAT,
		
		stealAttemptChance INT,
		stealAttempted INT,
		foldBbToStealChance INT,
		foldedBbToSteal INT,
		foldSbToStealChance INT,
		foldedSbToSteal INT,
		
		street1CBChance INT,
		street1CBDone INT,
		street2CBChance INT,
		street2CBDone INT,
		street3CBChance INT,
		street3CBDone INT,
		street4CBChance INT,
		street4CBDone INT,
		
		foldToStreet1CBChance INT,
		foldToStreet1CBDone INT,
		foldToStreet2CBChance INT,
		foldToStreet2CBDone INT,
		foldToStreet3CBChance INT,
		foldToStreet3CBDone INT,
		foldToStreet4CBChance INT,
		foldToStreet4CBDone INT,
		
		totalProfit INT,
		
		street1CheckCallRaiseChance INT,
		street1CheckCallRaiseDone INT,
		street2CheckCallRaiseChance INT,
		street2CheckCallRaiseDone INT,
		street3CheckCallRaiseChance INT,
		street3CheckCallRaiseDone INT,
		street4CheckCallRaiseChance INT,
		street4CheckCallRaiseDone INT);

INSERT INTO Settings VALUES (76);
INSERT INTO Sites ("name", currency) VALUES ('Full Tilt Poker', 'USD');
INSERT INTO Sites ("name", currency) VALUES ('PokerStars', 'USD');
INSERT INTO TourneyTypes (buyin, fee, knockout, rebuyOrAddon) VALUES (0, 0, 0, FALSE);
