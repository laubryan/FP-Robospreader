begin;

/* Create fields table */
drop table if exists fields;
create table fields(
	id integer primary key,
	name text not null,
	actual_value text,
	extracted_value text
	);

/* Populate fields for Test 1 */
insert into fields (id, name, actual_value)
values
	(0, "Accounts receivable", 1984),
	(1, "Inventories", 423),
	(2, "Current portion of contract assets", 1094),
	(3, "Other current assets", 714),
	(4, "Total current assets", 6343),
	(5, "Property, plant and equipment", 14049),
	(6, "Investments", 2554),
	(7, "Goodwill", 3923),
	(8, "Total assets", 40076),
	(9, "Short-term borrowings", 966),
	(10, "Income tax payable", 232),
	(11, "Other current liabilities", 126),
	(12, "Total current liabilities", 5748),
	(13, "Long-term-debt", 18375),
	(14, "Total liabilities", 29877);

/* Populate fields for Test 2 */
insert into fields (id, name, actual_value, extracted_value)
values
	(20, "Service", 20956, 20956),
	(21, "Product", 3218, 3218),
	(22, "Operating costs", 13975, 13975),
	(23, "Depreciation", 3660, 3660),
	(24, "Interest expense", 1146, 1146),
	(25, "Impairment of assets", 279, 279),
	(26, "Income taxes", 967, 967),
	(27, "Net earnings", 2926, 2920),
	(28, "Common shareholders", 2716, 2716),
	(29, "Preferred shareholders", 152, 157),
	(30, "Non-controlling interest", 58, 58),
	(31, "Common shareholders", 2716, 2716),
	(32, "Preferred shareholders", 152, 152),
	(33, "Non-controlling interest", 58, 58),
	(34, "Net earnings", 2926, 2926);

/* Create tests table */
drop table if exists tests;
create table tests(
	id integer primary key,
	test_id integer,
	field_id integer,
	foreign key(field_id) references fields(id),
	unique(test_id, field_id) on conflict replace
	);

/* Populate fields for Test 1 */
insert into tests (test_id, field_id)
select 1, id
from fields
where id < 20;

/* Populate fields for Test 2 */
insert into tests (test_id, field_id)
select 2, id
from fields
where id >=20;

/* Create results table */
drop table if exists results;
create table results(
	id integer primary key,
	test1_time integer,
	test1_errors integer,
	test2_time integer,
	test2_errors integer
	);

commit;