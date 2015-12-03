
/*
infos about italian fiscal code
http://www.agenziaentrate.gov.it/wps/content/Nsilib/Nsi/Home/CosaDeviFare/Richiedere/Codice+fiscale+e+tessera+sanitaria/Richiesta+TS_CF/SchedaI/Informazioni+codificazione+pf/

I'm supporter to light hungarian notation so 
in the variable names the prefix s is when a string/char is expected.
a when an array, i when integer, and f for float.

*/

/*
the italian tax office could assign to a tax payer a temporary fiscal code
or used for companies
this model is eleven digit: (from left to right)
7 are progressive number on the province, 3 digit identify the bureau in the province,
 last one is a control digit

return true, when seem valid
false otherwise
*/
function IsValidFiscalCode11( sCf )
{
	console.log( "verifico IsValidFiscalCodeTemporary",sCf)

	//regext to check the digits
	var reCfTemprary = /[\d]{11}/ig;
//

/*
precalculate tranformation of even position:
we mus double every number on even position,
because if each one has got two digits, must be reduced to on adding together.
e.g. an 8 on even position must be replaced with 8-> 8+8-> 16 -> 7
then sum the finded values.
*/
	var aTableEven=
	{
		0:0,
		1:2,
		2:4,
		3:6,
		4:8,
		5:1,
		6:3,
		7:5,
		8:7,
		9:9
	}

	var iControlDigit=0;
	if( sCf.length==11 && reCfTemprary.test( sCf ) )
	{
		console.log( "seem a tempory cf")

		console.log( "verifichiamo il caratere di controllo")
		//to check the control digit: now we summ the even 
		iControlDigit+= parseInt( sCf[1] )
		iControlDigit+= parseInt( sCf[3] )
		iControlDigit+= parseInt( sCf[5] )
		iControlDigit+= parseInt( sCf[7] )
		iControlDigit+= parseInt( sCf[9] )

		//we also add the odds
		iControlDigit+= parseInt( aTableEven[ sCf[0] ] )
		iControlDigit+= parseInt( aTableEven[ sCf[2] ] )
		iControlDigit+= parseInt( aTableEven[ sCf[4] ] )
		iControlDigit+= parseInt( aTableEven[ sCf[6] ] )
		iControlDigit+= parseInt( aTableEven[ sCf[8] ] )

		/*
		si sottrae da dieci la cifra relativa alle unità del precedente totale. 
		Il carattere di controllo è la cifra relativa alle unità del risultato.
		*/
		var iControlDigit= 10-(iControlDigit%10);

		if( sCf[10] == iControlDigit ) 
		{
			console.log( "iControlDigit calculated:", iControlDigit, " finded:", sCf[10] )
			return true
		}

	}

	return false
}




/*
calculate 3 lovercase alphas associated to surname
if there are  less than 3 conants, padded with vowels, 
also padded with X, so can't fail
function helper to check a surname against data packed in the cf

//Expected behavior
console.log( "calcutaleCfFromSurname" ,calcutaleCfFromSurname( "tonino" ) ,"-> 'tnn'" )
console.log( "calcutaleCfFromSurname" ,calcutaleCfFromSurname( "abci"   ) ,"-> 'bce'" )
console.log( "calcutaleCfFromSurname" ,calcutaleCfFromSurname(          ) ,"-> 'xxx'")
console.log( "calcutaleCfFromSurname" ,calcutaleCfFromSurname( "a"      ) ,"-> 'axx'")
console.log( "calcutaleCfFromSurname" ,calcutaleCfFromSurname( "aT"     ) ,"-> 'tax'")
*/
function calcutaleCfFromSurname( sSurnme )
{
	//in case of empty sSurnme, the result is 'xxx'
	if( !sSurnme ) 
		return 'xxx'

	//regular expression that accept vowels
	var reVowel= /[aeiou]/g

	//normalize sSurnme, converting to lovercase e stripping non alfabetical chars
	sSurnme = sSurnme.toLowerCase().match(/[a-z]/ig).join('');

	//from sSurnme get a string with all the vowels (keeping their relative order) 
	var sVowels = sSurnme.match( reVowel )||[] .join('')

	//get a sConsonants  from sSurnme without vowels (keeping their relative order)
	var sConsonants = sSurnme.replace( reVowel ,'')

	var sResult= sConsonants + sVowels +'xxx';

	return sResult.substring(0,3);
}



/*
calculate 3 lovercase alphas associated to surname
if there are  less than 3 conants, padded with vowels, 
also padded with X, so can't fail
function helper to check a name against data packed in the cf

//Expected behavior
console.log( calcutaleCfFromName( "bruno"      ) ,"-> 'brn'" )
console.log( calcutaleCfFromName( ""           ) ,"-> 'xxx'")
console.log( calcutaleCfFromName( "annalisa"   ) ,"-> 'nls'")
console.log( calcutaleCfFromName( "annunziata" ) ,"-> 'nnz'")
console.log( calcutaleCfFromName( "cdf"        ) ,"-> 'cdf'")
console.log( calcutaleCfFromName( "pa"         ) ,"-> 'pax'")
*/
function calcutaleCfFromName( sName )
{
	if( !sName ) 
		return 'xxx'

	//regular expression that accept vowels
	var reVowel= /[aeiou]/g

	//normalize sName, converting to lovercase e stripping non alfabetical chars
	sName = sName.toLowerCase().match(/[a-z]/ig).join('');

	//from sName get a sstring with all the vowels (keeping their relative order) 
	var sVowels = sName.match( reVowel )||[] .join('')

	//get a sConsonants  from sName without vowels (keeping their relative order)
	var sConsonants = sName.replace( reVowel ,'').substring(0,4)

	//in case of more then 3 consonants, the second one must be evicted
	if( sConsonants.length >3 ) 
	{
		var t=  sConsonants.split('')
		t.splice(1, 1)
		sConsonants= t.join('');
	}

	return ( sConsonants + sVowels +'xxx' ).substring(0,3);
}



//in order to check we need to recalcolate the control check
function recalcutaleControlDigitCf16( sCf )
{
	
	// table to calculate the control digit
	var aValori=
	[
		[
			1,0,5,7,9,13,15,17,19,21
			,1,0,5,7,9,13,15,17,19,21
			,2,4,18,20,11,3,6,8,12,14
			,16,10,22,25,24,23
		],
		[
			0,1,2,3,4,5,6,7,8,9
			,0,1,2,3,4,5,6,7,8,9
			,10,11,12,13,14,15,16,17,18,19
			,20,21,22,23,24,25
		]
	]

	if(sCf)
	{
		//this table is used to lookup in aValori as array, preferred instead of array because is more efficent
		var covertCharToIntTable=
		{
			"0":0,"1":1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9
			,"a":10,"b":11,"c":12,"d":13,"e":14,"f":15,"g":16,"h":17,"i":18,"j":19
			,"k":20,"l":21,"m":22,"n":23,"o":24,"p":25,"q":26,"r":27,"s":28,"t":29
			,"u":30,"v":31,"w":32,"x":33,"y":34,"z":35
		}

		sCf= sCf.toLowerCase()

		var sCf= sCf.substring(0,15) .toLowerCase()
		console.log( "sCf!",sCf)

		len= sCf.length
		var sum=0 

		//permorm transormation on even or odd order digit
		for( var i=0; i<len; i++ )
			sum+= aValori[ i%2 ][ covertCharToIntTable[ sCf[ i ] ] ]

		sum= sum%26

		//transform the control number in control char
		var aTransformIntToChar=[
			"a","b","c","d","e"
			,"f","g","h","i","j"
			,"k","l","m","n","o"
			,"p","q","r","s","t"
			,"u","v","w","x","y","z"
		]

		return aTransformIntToChar[sum]
	}
	return ""
}

/*
check for identify an omocodia,
is possible detece the progressive number identifing a fiscal code
for each code could be one strigth fiscal code with no omocodia,
and at maximum 128 code rimapped encoding the number in the fiscal code with string

this  function return an integer, 0 mean no omocodia, 
4 mean that this code is 4omocodic fiscal code (pointing to the straigth version)
*/
function checkOmocodiaCf16( sCf )
{
	if( !sCf )
		return 0

	var reOmocode = /[lmnpqrstuv]/ig;

	var tmp

	var iOmocodia= 0;
	var aOmocodiaPosition=[ 14,13,12,10,9,7,6 ]

	/*if the cf is shorter than expected we would calculate anyway 
	if the cf sound omocodic*/
	var iMax=sCf.length
	var tmp=[]
	var i
	for( i=0; i<aOmocodiaPosition.length; i++ )
	{
		if(aOmocodiaPosition[i]<iMax)
			tmp.push( aOmocodiaPosition[i] )
	}	
	aOmocodiaPosition= tmp;

	/*
	There is an omocodia when a fiscal code is not unique
	in other words there are distinct people with the the same fiscal code,
	In computer slang we could say that when we call "omocodia" when there is a the fiscal hash collapse.
	to solve this condition the italian tax bureau 
	must replace the numbers with letter (from left to right).
	Because there are 7 numbers that can be replaced with a corrispondent number
	this is the map of the encoding  with omocodia:
	0->L    5->R
	1->M    6->S
	2->N    7->T
	3->P    8->U
	4->Q    9->V

	there could be 2^7 combination of the same fiscal code.
	Omocodia a rare, but on average year there are ~1400 new omocodia.
	  */
	for( var i=0; i<aOmocodiaPosition.length; i++ )
	{		
		//tmp= sCf[ aOmocodiaPosition[i] ]
		//if( reOmocode.test( tmp ) )
		if( reOmocode.test( sCf[ aOmocodiaPosition[i] ] ) )
		{
			iOmocodia+= Math.pow(2,i)
		}
	}

	console.log( "---omocodia:--" ,iOmocodia )

	return iOmocodia;
}



function IsValidFiscalCode16( sCf )
{
	//we check parameter and lenght of fiscal code
	if( !sCf || sCf.length != 16 )
	{
		console.log( "the fiscal code is missing or shorter than expected:",sCf )
		return false
	}

	sCf= sCf.toLowerCase()

	//check the digit related to surname, 3 digit [a-z] or X
	var regex= /[A-Z]{3}/ig;
	var s_surname= sCf.substring( 0,3 )
	if( !regex.test( s_surname ) )
	{
		console.log( "the surname is malformed" ,s_surname )
		return false
	}



	//ve check the provided cf
	var l_name= /[A-Z]{3}/ig;
	var s_name= sCf.substring( 3,6 )
	if( !l_name.test( s_name ) )
	{
		console.log( "the name is malformed" ,s_name )
		return false
	}



	var n_year= /[0-9L-V]{2}/ig;
	var s_year= sCf.substring( 6,8 )
	if( !n_year.test( s_year ) )
	{
		console.log( "Year not valid" ,s_year )
		return false
	}

	var n_month= /[ABCDEHLMPRST]{1}/ig;
	var s_month= sCf.substring( 8,9 )
	if( !n_month.test( s_month ) )
	{
		console.log( "Month not valid" ,s_month )
		return false
	}

	var n_day= /[0-9L-V]{2}/ig;
	var s_day= sCf.substring( 9,11 )
	if( !n_day.test( s_day ) )
	{
		console.log( "Day not valid" ,s_day )
		return false
	}

	var l_town= /[A-MZ]{1}/ig;
	var s_town= sCf.substring( 11,12 )
	if( !l_town.test( s_town ) )
	{
		console.log( "the Town letter is wrong" ,s_town )
		return false
	}

	var n_town= /[0-9L-V]{3}/ig;
	var s_town= sCf.substring( 12,15 )
	if( !n_town.test( s_town ) )
	{
		console.log( "The Town number is wrong" ,s_town )
		return false
	}


	var sTown= sCf.substring( 11,12 );
	var iTown= parseInt( sCf.substring( 12,15 ) )||0;
	//console.log( "sCodiceComune",sTown ,iTown )

	if( sTown && iTown )
	{
		/* the town codes are on november 2015 from A001,A002 till M348 */
		if( iTown <1 || (sTown== 'M' && iTown>348 )  || (sTown== 'Z' && iTown>907 )  )
		{
			console.log( "Town with wrong code (>M348)",iTown )
			return false;
		}
	}



	//now we give a fast check of the control digit
	var l_last= /[A-Z]{1}/ig;
	var s_last= sCf.substring( 15,16 )
	if( !l_last.test( s_last ) )
	{
		console.log( "il lettera check NON va bene" ,s_last )
		return false
	}


	var tmp= recalcutaleControlDigitCf16(sCf)
	if(  s_last !=  tmp )
	{
		console.log( "the control digit is not ok" ,s_last, tmp )
		return false
	}
	else
		console.log( "Codice controllo calcolato ok"  )


return true;
}




//Here is the fiscal code of a fictitious Matteo Moretti 
//(male), born in Milan on 9 April 1925
//MRTMTT25D09F205Z

//Here is the fiscal code of a fictitious Samantha Miller 
//(female), born in the USA on 25 September 1982, living in Italy:
//MLLSNT82P65Z404U


//IsValidFiscalCode16( 'MLLSNT82P65Z404U' );
//IsValidFiscalCode16( 'MRTMTT25D09F205Z' );

//checkOmocodiaCf16(   'MRTMTT25DF9F205Z' )
//checkOmocodiaCf16(   'MLLSNT82P65Z404U' )

