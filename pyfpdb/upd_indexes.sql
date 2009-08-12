
# script to update indexes on mysql (+other?) database

select '1. Dropping indexes' as ' ';
select 'Can''t drop messages indicate index already gone' as ' ';

ALTER TABLE `fpdb`.`Settings` DROP INDEX `id`;
ALTER TABLE `fpdb`.`Sites` DROP INDEX `id`;
ALTER TABLE `fpdb`.`Gametypes` DROP INDEX `id`;
ALTER TABLE `fpdb`.`Players` DROP INDEX `id`;
ALTER TABLE `fpdb`.`Autorates` DROP INDEX `id`;
ALTER TABLE `fpdb`.`Hands` DROP INDEX `id`;
ALTER TABLE `fpdb`.`BoardCards` DROP INDEX `id`;
ALTER TABLE `fpdb`.`TourneyTypes` DROP INDEX `id`;
ALTER TABLE `fpdb`.`Tourneys` DROP INDEX `id`;
ALTER TABLE `fpdb`.`TourneysPlayers` DROP INDEX `id`;
ALTER TABLE `fpdb`.`HandsPlayers` DROP INDEX `id`;
ALTER TABLE `fpdb`.`HandsActions` DROP INDEX `id`;
ALTER TABLE `fpdb`.`HudCache` DROP INDEX `id`;

select '2. Adding extra indexes on useful fields' as ' ';
select 'Duplicate key name messages indicate new indexes already there' as ' '; 

ALTER TABLE `fpdb`.`tourneys` ADD INDEX `siteTourneyNo`(`siteTourneyNo`);
ALTER TABLE `fpdb`.`hands` ADD INDEX `siteHandNo`(`siteHandNo`);
ALTER TABLE `fpdb`.`players` ADD INDEX `name`(`name`);

