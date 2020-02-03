<?php 
require("db.php");
class MyModel extends MySQL {
    public function __construct() {
        parent::__construct();
    }
    public function calog2db() {
        $file = fopen(CALL_LOG_FILE, 'r');
        while (($l = fgetcsv($file)) !== FALSE) {
           
            $sql = " INSERT INTO  call_log 
            SET 
                accountcode ='".$l[0]."',
                caller_no ='".$l[1]."',
                dial_no ='".$l[2]."',
                extension ='".$l[3]."',
                lastapp ='".$l[7]."',
                start_at ='".$l[9]."',
                end_at ='".$l[11]."',
                duration ='".$l[12]."',
                disposition ='".$l['14']."'
            ";
            $query = $this->query($sql);
        }
        fclose($file);
        file_put_contents(CALL_LOG_FILE, ''); 
    }
	
	
	public function getLastCart($customer_id) {
		$sql = "SELECT max(order_id) as cartid FROM cart_master
					WHERE customer_id = '$customer_id' ";
        $query = $this->query($sql);
		return $query->row['cartid'];
	}
	public function startCall($phone_number) {
        $phone_number = trim(str_replace("+", "", $phone_number));
        $sql = "SELECT 	customer_id FROM  customer WHERE customer_no = '$phone_number' and client_id = 2 ";
        $query = $this->query($sql);
        
		if($query->num_rows){
            $custid = $query->row['customer_id'];
            $sql = "update customer set add_date = now() where customer_id = '$custid' ";
            $query = $this->query($sql);
		} else {
			$sql = "insert into customer set customer_no = '$phone_number', 
								client_id = 2, customer_status = 1, add_date = now() ";
			$query = $this->query($sql);
			$custid = $this->getLastId();
		}
		$sql = "insert into cart_master set hotel_id=1, customer_id=$custid, 
					client_id = 2, add_time = now(), cart_status='1' ";
		$query = $this->query($sql);
		$calogid = $this->getLastId();
		return array('status'=>1,'msg'=>'Success','call_log_id'=>$calogid,'customer_id'=>$custid);
		
    }
    public function setCallerName($phone_number,$caller_name) {
        $phone_number = trim(str_replace("+", "", $phone_number));
        $sql = "SELECT 	customer_id FROM   customer WHERE customer_no = '$phone_number' and client_id = 2 ";
        $query = $this->query($sql);
        $cond = "";
        if($caller_name!=""){
            $cond = " customer_name='$caller_name', ";
        }
		
		if($query->num_rows){
			$custid = $query->row['customer_id'];
			$sql = "update customer set $cond add_date=now() where customer_id = '$custid' ";
			$query = $this->query($sql);
		} else {
			$sql = "insert into customer set  $cond customer_no = '$phone_number', 
								client_id = 2, customer_status = 1, add_date = now() ";
			$query = $this->query($sql);
			$custid = $this->getLastId();
		}
		return array('status'=>1,'msg'=>'Success');
    }
    public function priceV5($json) {
        $req = json_decode($json,true);
		$print = 0;
        extract($req);
        $code = 0;
        $msg = "";
        $hotel_id = 1;
        $client_id = 0;
        $customer_id = 0;
        $order_price = 0;
        
        $index = 0;
       
        $code.=3;
        $products = array();
        $sum = 0;
        
        foreach($food as $k=>$a){
            $qty = $a['quantity']*1;
            $size = $a['package'];
            //$cat = strtolower(str_replace(" ","",$a['food_category']));

            $price = 0;
            
            $name = $a['food_item'];
            $note = $a['custom'];
            $product_id = 0;

            $sql = "SELECT product_id, product_price FROM products WHERE product_name = '$name' ";
            
            $query = $this->query($sql);
            if($query->num_rows){
                $product_id = $query->row['product_id'];
                if($qty<=0){
                    $qty = $query->row['def_qty'];
                }
                $products[$index]['product_id'] = $product_id;
                $products[$index]['product_name'] = $name;
                $products[$index]['qty'] = $qty;
                $products[$index]['product_price'] = $query->row['product_price'];
                $products[$index]['note'] = $a['custom'];
                $price += $query->row['product_price'];
                //$sum = $sum + ($query->row['total']*1);

                $products[$index]['size_name'] = "";
                $products[$index]['sizpriz'] = 0;
                $products[$index]['flaovur_name'] = "";
                $products[$index]['flavpriz'] = 0;
            } 
        
            /* if($size!=""){
                $sql = "SELECT price
                        FROM size a
                        LEFT JOIN product_size b on a.size_id = b.size_id and product_id = $product_id
                        WHERE size_name = '$size' ";
                $query = $this->query($sql);
                if($query->num_rows){
                    $products[$index]['size_name'] = $size;
                    $products[$index]['sizpriz'] = $query->row['price'];
                    $price += $query->row['price'];
                }
            } else {
                $sql = "SELECT size_name, price
                        FROM size a
                        LEFT JOIN product_size b on a.size_id = b.size_id and product_id = $product_id
                        WHERE is_default = 1 ";
                $query = $this->query($sql);
                if($query->num_rows){
                    $products[$index]['size_name'] = $query->row['size_name'];
                    $products[$index]['sizpriz'] = $query->row['price'];
                    $price += $query->row['price'];
                }
            } */

            $modist = "";
            $modifier = $a['modifier'];
            if($modifier!=""){
                $modist =  implode("','",$modifier);
                //GROUP_CONCAT(flaovur_name) as flaovur_name,  sum(price+flaovur_price) as flavpriz,is_pack
                //group by a.product_id
                $sql = "SELECT GROUP_CONCAT(flaovur_name) as flaovur_name,  
                            sum(price+flaovur_price) as flavpriz,max(is_pack=1) as pack
                        FROM product_flaovur a
                        INNER JOIN flaovur b on a.flaovur_id = b.flaovur_id and del_status = 0 and flaovur_name in ('$modist')
                        INNER JOIN modifier_groups c on b.mg_id = c.mg_id 
                        where product_id = '$product_id' and 
                        if('$size'!='' and is_pack=1,'$size',alt_name)=alt_name 
                        group by a.product_id";
                
                $query = $this->query($sql);
                if($query->num_rows){
                    $products[$index]['flaovur_name'] = $query->row['flaovur_name'];
                    $products[$index]['flavpriz'] = $query->row['flavpriz'];
                    $price +=$query->row['flavpriz'];
                }
            }
            $products[$index]['total'] = $price*$qty;
            $sum += $price*$qty;
            $index++;
                
        }

        
        
        if($sum>=0){

            $taxes = array();
            $tax_amt = 0;

            $sql = "SELECT 	tax_id,tax_type,tax_amt FROM  hotel_taxes WHERE hotel_id = 1 ";
			//if($print) print_r($sql);
            $query = $this->query($sql);
            if($query->num_rows){
                foreach($query->rows as $a){
					
                    if($a['tax_type'] == 'f'){
                        $taxes[] = array('tax_id'=>$a['tax_id'],'tax_amt'=>$a['tax_amt']);
                        $tax_amt = $tax_amt + ($a['tax_amt']);
                    } else {
                        $tmp = $sum*($a['tax_amt']/100);
                        $taxes[] = array('tax_id'=>$a['tax_id'],'tax_amt'=>$tmp);
                        $tax_amt = $tax_amt + $tmp;
                    }
                }
            }
            //$sum + $tax_amt
            $order_price = round($sum,2);
        }
        return array('total_price'=>$order_price,'resp_status'=>1,'food_price'=>$sum,
                    'tax_price'=>$tax_amt);

    }


    public function makeOrderV5($json,$callforward=0) {
        $req = json_decode($json,true);
        extract($req);
        $code = 0;
        $msg = "";
        $hotel_id = 0;
        $client_id = 0;
        $customer_id = 0;
        $custname = "";
        
        
        if(isset($extension)){
            //extension = '$extension'
            $sql = "SELECT 	hotel_id,client_id FROM  hotels WHERE hotel_id='1' ";
            $query = $this->query($sql);
            if($query->num_rows){
                $hotel_id = $query->row['hotel_id'];
                $client_id = $query->row['client_id'];
                $code.=1;
                $customer_id = 0;
                
                if(isset($phone_number)){
                    $phone_number = trim(str_replace("+", "", $phone_number));
                    $sql = "SELECT 	customer_id,customer_name FROM  customer WHERE customer_no = '$phone_number' 
								and client_id = '$client_id' ";
                    $query = $this->query($sql);
                    if($query->num_rows){
                        $customer_id = $query->row['customer_id'];
                        $custname = $query->row['customer_name'];
                        if($custname=="" && $caller_name!=""){
                            $custname = $caller_name;
                            $sql = "update customer set customer_name='$caller_name' 
							where customer_id = '$customer_id' ";
                            $query = $this->query($sql);
                        }
                        /*if($caller_name!=""){
                            $sql = "update customer set customer_name='$caller_name' 
							where customer_id = '$customer_id' ";
                            $query = $this->query($sql);
                        }*/
                    }/* else {
                        $sql = "insert into customer set customer_name='$caller_name',customer_no = '$phone_number', 
                                client_id = '$client_id', customer_status = 1, add_date = now() ";
                        $query = $this->query($sql);
                        $customer_id = $this->getLastId();
                    }
                    $code.=2;*/
                } else {
                    $msg .=' Phone number is missing. ';
                }

            } else {
                $msg .=' No extension available. ';
            }
        } else {
            $msg .=' Extension is missing. ';
        }

        

        if($hotel_id > 0 && $customer_id >0){
            $code.=3;
            $products = array();
            $sum = 0;
            $index = 0;
			$cartid = $this->getLastCart($customer_id);
			
            foreach($food as $k=>$a){
                $qty = $a['quantity']*1;
                $size = $a['package'];
                //$cat = strtolower(str_replace(" ","",$a['food_category']));

                $price = 0;
                
                $name = $a['food_item'];
                $note = $a['custom'];
                $product_id = 0;
                

                $sql = "SELECT product_id, product_price, pos_id
                        FROM products
                        WHERE product_name = '$name' ";
                
                $query = $this->query($sql);
                if($query->num_rows){
                    $product_id = $query->row['product_id'];
                    if($qty<=0 && $callforward==0){
                        $qty = $query->row['def_qty'];
                    }
                    $products[$index]['product_id'] = $product_id;
                    $products[$index]['pos_id'] = $query->row['pos_id'];
                    $products[$index]['posids'] = "";
                    $products[$index]['product_name'] = $name;
                    $products[$index]['qty'] = $qty;
                    $products[$index]['product_price'] = $query->row['product_price'];
                    $products[$index]['note'] = $a['custom'];
                    $price += $query->row['product_price'];
                    //$sum = $sum + ($query->row['total']*1);

                    $products[$index]['size_name'] = "";
                    $products[$index]['sizpriz'] = 0;
                    $products[$index]['flaovur_name'] = "";
                    $products[$index]['flavpriz'] = 0;
                } 
            
                /* if($size!=""){
                    $sql = "SELECT price
                            FROM size a
                            LEFT JOIN product_size b on a.size_id = b.size_id and product_id = $product_id
                            WHERE size_name = '$size' ";
                    $query = $this->query($sql);
                    if($query->num_rows){
                        $products[$index]['size_name'] = $size;
                        $products[$index]['sizpriz'] = $query->row['price'];
                        $price += $query->row['price'];
                    }
                } else {
                    $sql = "SELECT size_name, price
                            FROM size a
                            LEFT JOIN product_size b on a.size_id = b.size_id and product_id = $product_id
                            WHERE is_default = 1 ";
                    $query = $this->query($sql);
                    if($query->num_rows){
                        $products[$index]['size_name'] = $query->row['size_name'];
                        $products[$index]['sizpriz'] = $query->row['price'];
                        $price += $query->row['price'];
                    }
                } */

                $modist = "";
                $mgids = "";
                $modifier = $a['modifier'];
                if($modifier!=""){
                    $modist =  implode("','",$modifier);
                    $sql = "SELECT GROUP_CONCAT(flaovur_name ORDER BY is_food DESC) as flaovur_name,  sum(price+flaovur_price) as flavpriz,
                                GROUP_CONCAT(b.pos_id) as posids,max(is_pack=1) as size_name,
                                GROUP_CONCAT(QUOTE(alt_name)) as mgids
                            FROM product_flaovur a
                            INNER JOIN flaovur b on a.flaovur_id = b.flaovur_id and  flaovur_name in ('$modist')
                            INNER JOIN modifier_groups c on b.mg_id = c.mg_id 
                            where product_id = '$product_id' and del_status = 0 and 
                            if('$size'!='' and is_pack=1,'$size',alt_name)=alt_name 
                            group by a.product_id";
                    
                    $query = $this->query($sql);
                    if($query->num_rows){
                        $products[$index]['flaovur_name'] = $query->row['flaovur_name'];
                        $products[$index]['flavpriz'] = $query->row['flavpriz'];
                        $products[$index]['posids'] = $query->row['posids'];
                        $products[$index]['size_name'] = "";
                        if($query->row['size_name'])
                            $products[$index]['size_name'] = $size;
                        $price +=$query->row['flavpriz'];
                        $mgids = $query->row['mgids'];
                        
                    }
                }
                $cond = "";
                if($mgids!=""){
                    $cond = " and alt_name not in ($mgids) ";
                }
                $sql = "SELECT  GROUP_CONCAT(flaovur_name) as flaovur_name,  sum(price+flaovur_price) as flavpriz,
                                GROUP_CONCAT(b.pos_id) as posids
                        FROM product_flaovur a
                        INNER JOIN flaovur b on a.flaovur_id = b.flaovur_id 
                        INNER JOIN modifier_groups c on b.mg_id = c.mg_id and 	is_food =0 and 	is_pack = 0
                        where product_id = '$product_id' and del_status = 0 and is_default = 1  $cond
                        group by a.product_id
                        ";
                
                $query = $this->query($sql);
                if($query->num_rows){
                    $products[$index]['flaovur_name'] .= ",".$query->row['flaovur_name'];
                    $products[$index]['flavpriz'] += $query->row['flavpriz'];
                    $products[$index]['posids'] .= ",".$query->row['posids'];
                    $products[$index]['size_name'] = "";
                    $price +=$query->row['flavpriz'];
                }

                $products[$index]['total'] = $price*$qty;
                $sum += $price*$qty;
                $index++;
                   
            }
            
            if($sum>=0){

                $taxes = array();
                $tax_amt = 0;

                $sql = "SELECT 	tax_id,tax_type,tax_amt FROM  hotel_taxes WHERE hotel_id = '$hotel_id' ";
                $query = $this->query($sql);
                if($query->num_rows){
                    foreach($query->rows as $a){
                        if($a['tax_type'] == 'f'){
                            $taxes[] = array('tax_id'=>$a['tax_id'],'tax_amt'=>$a['tax_amt']);
                            $tax_amt = $tax_amt + ($a['tax_amt']);
                        } else {
                            $tmp = $sum*($a['tax_amt']/100);
                            $taxes[] = array('tax_id'=>$a['tax_id'],'tax_amt'=>$tmp);
                            $tax_amt = $tax_amt + $tmp;
                        }
                    }
                }
                
                $code.=4;
                
                $order_price = round($sum + $tax_amt,2);
				
				if($callforward==1){
					$sql = "update cart_master set  product_price = $sum , tax_amt = $tax_amt, 
							order_price=$order_price,   
                            add_time = now(), special_note = '$special_note', cart_status='2'
							where order_id= $cartid ";
    	            $query = $this->query($sql);
        	        $order_id = $cartid;
                
					foreach($products as $a){
						$sql = "insert into cart_details set order_id='$order_id', 
						product_id = '".$a['product_id']."', product_name = '".$a['product_name']."', product_price = '".$a['product_price']."', 
						size_name = '".$a['size_name']."',  flaovur_name = '".$a['flaovur_name']."', 
						size_price = '".$a['sizpriz']."', flaovur_price = '".$a['flavpriz']."',posids = '".$a['posids']."',
						quantity = '".$a['qty']."', total_price = '".$a['total']."', note = '".$a['note']."' ";
	
						$query = $this->query($sql);
					}
					
					if(isset($unfound)){
						
						$sql = "insert into cart_details set order_id='$order_id',
							product_name='".$this->escape($unfound)."'";
						$query = $this->query($sql);
						
					}
					
					return array('status'=>1);
				} else {
					
	                $sql = "insert into order_master set hotel_id='$hotel_id',customer_id = '$customer_id', 
                            client_id = '$client_id', product_price = $sum , tax_amt = $tax_amt, 
							order_price=$order_price,   
                            add_time = now(), 	status_id = 1, special_note = '$special_note' ";
    	            $query = $this->query($sql);
        	        $order_id = $this->getLastId();
					
					foreach($products as $a){
                        if($a['product_id']>0){
						$sql = "insert into order_details set order_id='$order_id', 
						product_id = '".$a['product_id']."', product_name = '".$a['product_name']."', product_price = '".$a['product_price']."', 
						size_name = '".$a['size_name']."',  flaovur_name = '".$a['flaovur_name']."', 
						size_price = '".$a['sizpriz']."', flaovur_price = '".$a['flavpriz']."',posids = '".$a['posids']."',
						quantity = '".$a['qty']."', total_price = '".$a['total']."', note = '".$a['note']."' ";
	
                        $query = $this->query($sql);
                        }
					}
					foreach($taxes as $a){
						$sql2 = "insert into order_taxes set order_id='$order_id', tax_id = '".$a['tax_id']."', tax_amt = '".$a['tax_amt']."' ";
						$query = $this->query($sql2);
					}
                    
                    $spnote="No:".$phone_number;
                    if($custname!="")
                        $spnote .= ", Name:".$custname;
                    if($special_note!="")
                        $spnote .=", Note:".$special_note;
                    
					$this->cloverorder($order_price,$order_id,$products,$spnote);
                    $print = $this->isPrinted($order_id,0);
                    
                    $printstatus = 4;
                    if($print){
                        $printstatus = 3;
                    }
                    $sql = "update cart_master set order_price=$order_price,   
                            add_time = now(),org_order_id = '$order_id', cart_status=$printstatus
							where order_id= $cartid ";
    	            $query = $this->query($sql);
                    
	
					return array('order_status'=>'Inprogress','order_id'=>$order_id,'product_price'=>$sum,'tax_amt'=>$tax_amt,'total_price'=>$order_price,'products'=>$products,'resp_status'=>1,'Print'=>$print);
				}
            }
        }
        
        return array('order_status'=>'','order_id'=>0,'total_price'=>0,'resp_status'=>0,'code'=>$code,'msg'=>$msg);
    }
	
	public function isPrinted($order_id,$cnt){
		$printed = 0;
		if($cnt>5) return 0;
		sleep(5);
		$sql = "SELECT 	1 FROM  order_master WHERE order_id = '$order_id' and print_status='DONE' ";
		$query = $this->query($sql);
		if($query->num_rows){
			return 1;
		} else {
			$cnt++;
			return $this->isPrinted($order_id,$cnt);
		}
	
	}

    
    public function cloverorder($order_price,$cmsorderid,$products,$spnote){
        $hotel_id = 1;
        $client_id = 1;
        $data = array();
            
        $data['employee']['id']   = CLOVER_EMP;
        $data['orderType']['id']  =   CLOVER_ORDERTYPE;
        $data['title']            = "#".$cmsorderid;
        //$data['title']            = "LIVA_BOT";
        $data['note']            = $spnote;
        $data['currency']          = "USD";
        $data['state']             = "Paid";
		$data['paymentState']      = "PAID";
        $data['groupLineItems']    = "true";
        $data['manualTransaction'] = "false";
        $data['testMode']         = "false";
        $data['taxRemoved']       = "false";
        $data['isVat']            = "true";
        $data['total']            = ($order_price*100);
        
        
        $order = $this->curlpost('orders',$data);
        $order_id = $order['id'];

       /*  print_r($data);
        print_r($products); */
        

        
        foreach($products as $a){
            $altid = "";
            if($a['size_name']!=""){
                $altid = $this->getPackProId($a['product_id'],$a['size_name']);
            }
            for($i=1;$i<=$a['qty'];$i++){
                $data = array();
                if($altid!="") $data['item']['id'] = $altid;
                else $data['item']['id'] = $a['pos_id'];
            
                /* print_r($data);
                die; */
                $fun = 'orders/'.$order_id.'/line_items';
                $line = $this->curlpost($fun,$data);
                $item_id = $line['id'];
                if($a['posids']!=""){
                    $modi = explode(",",$a['posids']);
                    foreach($modi as $b){
                        if($b!=""){
                            $data = array();
                            $data['modifier']['id'] = $b;
                            $fun = 'orders/'.$order_id.'/line_items/'.$item_id.'/modifications';
                            $line = $this->curlpost($fun,$data);
                        }
                    }
                }
            }
        }
        $sql = "update order_master set pos_id='$order_id', update_time=now() where order_id = $cmsorderid  ";
        $query = $this->query($sql);
        
    }
    public function cloverordercron(){
        $hotel_id = 1;
        $client_id = 1;
        $data = array();

        $sql = "SELECT order_id,order_price FROM  order_master WHERE hotel_id = '$hotel_id' and pos_id='' and status_id=1 order by add_time limit 0,1 ";
        $query = $this->query($sql);
        if($query->num_rows){
            $tot = $query->row['order_price'];
            $orderid = $query->row['order_id'];

            $sql = "SELECT a.product_id,pos_id,posids,quantity, size_name
                FROM  order_details a
                INNER join products b on a.product_id = b.product_id
                WHERE  order_id =  $orderid ";
            $query = $this->query($sql);
            $items = $query->rows;
            
            
            $data['employee']['id']   = CLOVER_EMP;
            $data['orderType']['id']  =   CLOVER_ORDERTYPE;
            $data['title']            = "BOT#".$orderid;
            $data['currency']          = "USD";
            $data['state']             = "Open";
            $data['groupLineItems']    = "true";
            $data['manualTransaction'] = "false";
            $data['testMode']         = "false";
            $data['taxRemoved']       = "false";
            $data['isVat']            = "true";
            $data['total']            = ($tot*100);
            
            $order = $this->curlpost('orders',$data);
            $order_id = $order['id'];

            
            foreach($items as $a){
                $altid = "";
                if($a['size_name']!=""){
                    $altid = $this->getPackProId($a['product_id'],$a['size_name']);
                }
                for($i=1;$i<=$a['quantity'];$i++){
                    $data = array();
                    if($altid!="") $data['item']['id'] = $altid;
                    else $data['item']['id'] = $a['pos_id'];
                
                    $fun = 'orders/'.$order_id.'/line_items';
                    $line = $this->curlpost($fun,$data);
                    $item_id = $line['id'];
                    if($a['posids']!=""){
                        $modi = explode(",",$a['posids']);
                        foreach($modi as $b){
                            if($b!=""){
                                $data = array();
                                $data['modifier']['id'] = $b;
                                $fun = 'orders/'.$order_id.'/line_items/'.$item_id.'/modifications';
                                $line = $this->curlpost($fun,$data);
                            }
                        }
                    }
                }
            }
            $sql = "update order_master set pos_id='$order_id', update_time=now() where order_id = $orderid  ";
            $query = $this->query($sql);
        }
    }

    public function orderstatus(){
        $hotel_id = 1;
        $client_id = 1;
        $data = array();

        $avl = 0;
        $ins = "";

        $sql = "SELECT pos_id FROM  order_master WHERE hotel_id = '$hotel_id' and pos_id<>'' and status_id =1 and date(add_time) = curdate() ";
        $query = $this->query($sql);
        if($query->num_rows){
            $avl = 1;
            foreach($query->rows as $a){
                $items[$a['pos_id']] = 0;
            }
        }
        if($avl){
            $orders = $this->mycurl('orders?filter=state!=OPEN');
            foreach($orders['elements'] as $a){
                if(isset($items[$a['id']])){
                    $ins = "'".$a['id']."', ";
                }
            }
            $ins = rtrim($ins, ', ');
            if($ins!=""){
                $sql = "update order_master set status_id='2', update_time=now() where pos_id in ($ins)  ";
                $query = $this->query($sql);
            }
        }
    }
    
    public function getPackProId($proid,$pack) {
        $sql = "SELECT p.pos_id
                FROM products p
                INNER JOIN product_flaovur a on a.product_id = p.product_id
                INNER JOIN flaovur b on a.flaovur_id = b.flaovur_id and alt_name ='$pack'
                INNER JOIN modifier_groups c on b.mg_id = c.mg_id and is_pack = 1
                where product_status = 0 and p.product_id<> $proid
                group by p.product_id";
        
        $query = $this->query($sql);
        if($query->num_rows){
            return $query->row['pos_id'];
        }
        return '';
    }

    public function getinventory() {
        
        $hotel_id = 1;
        $client_id = 1;

        
        $tax_cms= array();
        $sql = "SELECT tax_id FROM  hotel_taxes WHERE hotel_id = $client_id ";
        $query = $this->query($sql);
        if($query->num_rows){
            foreach($query->rows as $a){
                $tax_cms[] = $a['tax_id'];
            }
        }
       
        
        $tax_pos = $this->mycurl('tax_rates');
//print_r($tax_pos);die;
        foreach($tax_pos['elements'] as $c){
            if($c['isDefault']){
                if(count($tax_cms)){
                    $sql = "update hotel_taxes set 	tax_name = '".$c['name']."', tax_amt ='".round($c['rate']/100000,2)."'
                             where hotel_id = $client_id ";
                    $query = $this->query($sql);
                } else {
                    $sql = "insert into hotel_taxes set hotel_id='$hotel_id' , tax_name = '".$c['name']."', tax_amt ='".round($c['rate']/100000,2)."',tax_type='p'";
                    $query = $this->query($sql);
                }
            }
        } 


        $cate_cms= array();
        $sql = "SELECT 	pos_id,category_id FROM  categories WHERE client_id = $client_id ";
        $query = $this->query($sql);
        if($query->num_rows){
            foreach($query->rows as $a){
                $cate_cms[$a['pos_id']] = $a['category_id'];
            }
        }
        
        $cate_pos = $this->mycurl('categories');
        foreach($cate_pos['elements'] as $c){
            if(!isset($cate_cms[$c['id']])){
               $sql = "insert ignore into  categories set pos_id = '".$c['id']."', category_name = '".$c['name']."', client_id='$client_id', category_status=1, add_date=now()";
               $query = $this->query($sql);
               $cat_id = $this->getLastId();
               $cate_cms[$c['id']] = $cat_id;
            } else {
                $sql = "update  categories set category_name = '".$c['name']."' where pos_id = '".$c['id']."' ";
                $query = $this->query($sql);
            }
        }
        

        $grp_pos = $this->mycurl('modifier_groups?expand=modifiers');
        
       
        $grp_cms= array();
        $sql = "SELECT 	pos_id,mg_id FROM  modifier_groups WHERE client_id = $client_id ";
        $query = $this->query($sql);
        if($query->num_rows){
            foreach($query->rows as $a){
                $grp_cms[$a['pos_id']] = $a['mg_id'];
            }
        }

        $flv_cms= array();
        $sql = "SELECT 	flaovur_id,pos_id FROM  flaovur WHERE client_id = $client_id ";
        $query = $this->query($sql);
        if($query->num_rows){
            foreach($query->rows as $a){
                $flv_cms[$a['pos_id']] = $a['flaovur_id'];
            }
        }
        
        foreach($grp_pos['elements'] as $c){
            
            if(!isset($grp_cms[$c['id']])){
               $sql = "insert ignore into  modifier_groups set pos_id = '".$c['id']."', mg_name = '".$c['name']."', client_id='$client_id', mg_status=1,is_food=1, add_date=now()";
               $query = $this->query($sql);
               $mg_id = $this->getLastId();
            } else {
                $sql = "update  modifier_groups set mg_name = '".$c['name']."' where pos_id = '".$c['id']."'";
                $query = $this->query($sql);
                $mg_id = $grp_cms[$c['id']];
            }
            foreach($c['modifiers']['elements'] as $a){
                if(!isset($flv_cms[$a['id']])){
                    $sql = "insert ignore into  flaovur set pos_id = '".$a['id']."',mg_id='".$mg_id."', 
                    flaovur_name = '".$a['name']."', flaovur_price = '".round($a['price']/100,2)."', alt_name = '".$c['name']."',
                    client_id='$client_id', flaovur_status=1, add_date=now()";
                    $query = $this->query($sql);
                    $flv_id = $this->getLastId();
                    $flv_cms[$a['id']] = $flv_id;
                 } else {
                     //flaovur_name = '".$a['name']."',
                    $sql = "update  flaovur 
                    set mg_id='".$mg_id."',  flaovur_price = '".round($a['price']/100,2)."'
                    where pos_id = '".$a['id']."' ";
                    $query = $this->query($sql);
                 }
            }
        }

       

        $pro_pos = $this->mycurl('items?expand=categories,modifierGroups');
       
        $pro_cms= array();
        $sql = "SELECT 	pos_id,product_id FROM  products WHERE client_id = $client_id ";
        $query = $this->query($sql);
        if($query->num_rows){
            foreach($query->rows as $a){
                $pro_cms[$a['pos_id']] = $a['product_id'];
            }
        }

        $pro_cat= array();
        $sql = "SELECT 	product_id,b.pos_id
                FROM  product_category a
                INNER JOIN categories b on a.category_id = b.category_id
                WHERE client_id = $client_id ";
        $query = $this->query($sql);
        if($query->num_rows){
            foreach($query->rows as $a){
                $pro_cat[$a['product_id']][$a['pos_id']] = 1;
            }
        }

        $pro_flv= array();
        $sql = "SELECT 	product_id,b.pos_id
                FROM  product_flaovur a
                INNER JOIN flaovur b on a.flaovur_id = b.flaovur_id
                WHERE client_id = $client_id ";
        $query = $this->query($sql);
        if($query->num_rows){
            foreach($query->rows as $a){
                $pro_flv[$a['product_id']][$a['pos_id']] = 1;
            }
        }

        foreach($pro_pos['elements'] as $c){
            if(!isset($pro_cms[$c['id']])){
                $sql = "insert ignore into  products set pos_id = '".$c['id']."', product_name = '".$c['name']."', 
                            product_price='".round($c['price']/100,2)."', client_id='$client_id', product_status=1, add_date=now()";
                $query = $this->query($sql);
                $pro_id = $this->getLastId();
             } else {
                 //product_name = '".$c['name']."', 
                $sql = "update products set product_price='".round($c['price']/100,2)."' where  pos_id = '".$c['id']."'";
                $query = $this->query($sql);
                 $pro_id = $pro_cms[$c['id']];
             }
            foreach($c['categories']['elements'] as $a){
                if(!isset($pro_cat[$pro_id][$a['id']])){
                    $sql = "insert ignore into  product_category set product_id = '".$pro_id."', category_id='".$cate_cms[$a['id']]."'";
                    $query = $this->query($sql);   
                }
            }

            foreach($c['modifierGroups']['elements'] as $a){
                $flv = explode(",",$a['modifierIds']);
                foreach($flv as $f){
                    if(!isset($pro_flv[$pro_id][$f])){
                        $sql = "insert ignore into  product_flaovur set product_id = '".$pro_id."', flaovur_id='".$flv_cms[$f]."'";
                        $query = $this->query($sql);   
                    }
                }
            }
             
        }
        //die;
        $this->getJson();
    }

    public function curlpost($fun,$data){
        $merchant_id = CLOVER_MID;
        $access_token = CLOVER_TOKEN;

        $json = json_encode($data);

        $url = 'https://api.clover.com/v3/merchants/' . $merchant_id . '/'.$fun;
        $curl = curl_init($url);
        curl_setopt($curl, CURLOPT_HTTPHEADER, array("Authorization:Bearer " . $access_token,'Content-Type: application/json' ));
        curl_setopt($curl, CURLOPT_POST, true);
        curl_setopt($curl, CURLOPT_POSTFIELDS, $json);
        curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1);
        $auth = curl_exec($curl);
        curl_close($curl);
        return json_decode($auth,true);
    }
    public function mycurl($fun){
        $merchant_id = CLOVER_MID;
        $access_token = CLOVER_TOKEN;

        $url = 'https://api.clover.com/v3/merchants/' . $merchant_id . '/'.$fun;
        $curl = curl_init($url);
        curl_setopt($curl, CURLOPT_HTTPHEADER, array("Authorization:Bearer " . $access_token,'Content-Type: application/json' ));
        curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1);
        $auth = curl_exec($curl);
        curl_close($curl);
        return json_decode($auth,true);
    }


    

   
    public function getHotelByExt($ext) {
        $sql = "SELECT 	hotel_id FROM  hotels WHERE extension = '$ext' ";
        $query = $this->query($sql);
        if($query->num_rows){
            return $query->row['hotel_id'];
        }
        return 0;
    }
    

    public function getCallerName($customer_no) {
        $sql = "SELECT 	customer_name FROM   customer WHERE customer_no = '$customer_no' ";
        $query = $this->query($sql);
        if($query->num_rows){
            return array('name'=>$query->row['customer_name'],'status'=>1);
        } else {
            return array('name'=>'','status'=>0);
        }
        
    }

    

    public function getJson(){
        $data = array();
        $data2 = array();
        $extra = array();
        $isna = array();
        
        $sql = "SELECT flaovur_name FROM  flaovur where is_na = 1";
        $query = $this->query($sql);
        if($query->num_rows){
            foreach($query->rows as $a){
                $isna[$a['flaovur_name']] =1;
            }
        }  
       
         $sql = "SELECT b.flaovur_name as product_name, c.flaovur_name, c.flaovur_price, pop_up, c.alt_name 
                FROM  subpro_modif a
                INNER JOIN flaovur b on a.product_id = b.flaovur_id
                INNER JOIN flaovur c on a.flaovur_id = c.flaovur_id
                LEFT JOIN modifier_groups d on c.mg_id = d.mg_id and mg_status = 1";
        
        $query = $this->query($sql);
        if($query->num_rows){
            foreach($query->rows as $a){
                $extra[$a['product_name']]['preperations'][$a['alt_name']]['name'] =$a['alt_name'];
                $extra[$a['product_name']]['preperations'][$a['alt_name']]['popup'] =$a['pop_up'];
                $extra[$a['product_name']]['preperations'][$a['alt_name']]['list'][$a['flaovur_name']] = $a['flaovur_price'];
            }
        }
        
        
        $sql = "SELECT product_name,product_price, alt_name, flaovur_name, flaovur_price,is_food,
                        pop_up,category_name,is_pack,is_modif,
                        case 
                            when b.product_id is not null and b.added_time > h.add_date then 'new'
                            when b.product_id is null and a.add_date > h.add_date then 'new'
                            else 'old'
                        end as stat
                FROM  products a
                LEFT JOIN product_flaovur b on a.product_id = b.product_id and del_status = 0
                LEFT JOIN flaovur c on b.flaovur_id = c.flaovur_id
                LEFT JOIN modifier_groups d on c.mg_id = d.mg_id and mg_status = 1
                LEFT JOIN product_category e on a.product_id = e.product_id
                LEFT JOIN categories f on e.category_id = f.category_id
                LEFT JOIN  hotels h on hotel_id = 1
                WHERE product_status = 1";
                //and product_name in('Luch Platters')
                //and product_name in('Biryani')
                //and product_name in('Fidaa Mixed Grill')
                //'Butter Milk',,'Veg. Entrees'
        //die;
        $query = $this->query($sql);
                
        if($query->num_rows){
            
            foreach($query->rows as $a){
                
                $data[$a['product_name']]['name'] =$a['product_name'];
                $data[$a['product_name']]['price'] =$a['product_price'];
                $data[$a['product_name']]['fstat'] =$a['stat'];
                if($a['category_name']!="")
                    $data[$a['product_name']]['categories'][$a['category_name']] =1;
                if($a['flaovur_name']!=""){
                    if($a['is_food']==1 && $a['is_modif']==0){
                        
                        if($a['is_pack']==1){
                            $data[$a['product_name']]['pack'][$a['alt_name']][$a['flaovur_name']] = $a['flaovur_price'];
                        } else {
                            $data[$a['product_name']]['modifiers'][$a['flaovur_name']] = $a['flaovur_price'];
                        }
                        $data[$a['product_name']]['mstat'][$a['flaovur_name']] = $a['stat'];
                    
                    } else {
                        $data[$a['product_name']]['preperations'][$a['alt_name']]['name'] =$a['alt_name'];
                        $data[$a['product_name']]['preperations'][$a['alt_name']]['popup'] =$a['pop_up'];
                        $data[$a['product_name']]['preperations'][$a['alt_name']]['list'][$a['flaovur_name']] = $a['flaovur_price'];
                    }
                }
            }
           
           //print_r($data);
           //die;
            $preperations = array();

           

            foreach($data as $a){
                $item = array();
                $popcnt = 0;
                $index = "";
                $tmprep = array();
                /* $item['categories'] = array();
                if(isset($a['categories']))
                foreach($a['categories'] as $k=>$c){
                    $item['categories'][]=$k;
                } */
                if(isset($a['preperations'])){
                    foreach($a['preperations'] as $p){
                        //$item['preperations'][] = $p;
                        $index = "";
                        if($p['popup']==1){
                            $popcnt++;
                        }
                        foreach($p['list'] as $k=>$l){
                            $index .= strtolower(str_replace(" ","",$k));
                        }
                        
                        $md5 = md5($index);
                        
                        if(!isset($preperations[$md5])){
                            //echo $index."--".$md5."\n";
                            $data2['preperations'][$md5] = $p;
                        }
                        $tmprep[] = $md5;
                    }
                }
                $pack =array();
                if(isset($a['pack'])){
                    foreach($a['pack'] as $k2=>$p1){    // k2 : Biryani Regular
                        foreach($p1 as $k3=>$p2){       // k3 : Egg Biryani
                            $pack[$k3][$k2] = $p2;
                        }
                    }
                    foreach($pack as $k3=>$p3){
                        $item[$k3]['state'] = $a['mstat'][$k3];
                        if(count($p3)>1){
                            $item[$k3]['popup_count'] = $popcnt;
                            $item[$k3]['pack'] = $p3;
                            $item[$k3]['preperations'] = $tmprep;
                            $item[$k3]['is_pack'] = 1;

                        } else {
                            $item[$k3]['popup_count'] = $popcnt;
                            $item[$k3]['is_pack'] = 0;
                            foreach($p3 as $price)
                                $item[$k3]['price'] = $price;

                            $item[$k3]['preperations'] = $tmprep;
                        }
                        $item[$k3]['state'] = $a['mstat'][$k3];

                    }
                    
                } else if(isset($a['modifiers'])){
                    foreach($a['modifiers'] as $k1=>$b){
                        $item[$k1]['state'] = $a['mstat'][$k1];
                        if(isset($isna[$k1])){
                            $item[$k1]['popup_count'] = 0;
                            $item[$k1]['is_pack'] = 0;
                            $item[$k1]['price'] = $b;
                            $item[$k1]['preperations'] = array();
                        } else {
                            $item[$k1]['popup_count'] = $popcnt;
                            $item[$k1]['is_pack'] = 0;
                            $item[$k1]['price'] = $b;
                            $item[$k1]['preperations'] = $tmprep;
                        }
                        
                    }
                } else {
                    $item[$a['name']]['state'] = $a['fstat'];
                    $item[$a['name']]['price'] = $a['price'];
                    $item[$a['name']]['popup_count'] = $popcnt;
                    $item[$a['name']]['is_pack'] = 0;
                    $item[$a['name']]['preperations'] = $tmprep;
                }

                
                
                
                $data2['food_items'][$a['name']] = $item;
            } 
            //print_r($data2);
            //die;
            $data3 = $data2;

            foreach($data2['food_items'] as $k1=>$a){
                foreach($a as $k2=>$b){
                    if(isset($extra[$k2])){
                        $item = array();
                        $popcnt = 0;
                        $index = "";
                        $tmprep = array();
                       
                        if(isset($extra[$k2]['preperations'])){
                           
                            foreach($extra[$k2]['preperations'] as $p){
                                
                                if($p['popup']==1){
                                    $popcnt++;
                                }
        
                                foreach($p['list'] as $k=>$l){
                                    $index .= strtolower(str_replace(" ","",$k));
                                }
                                $md5 = md5($index);
                                if(!isset($preperations[$md5])){
                                    $data3['preperations'][$md5] = $p;
                                }
                                $tmprep[] = $md5;
                            }
                            
                            $data3['food_items'][$k1][$k2]['preperations']=$tmprep;
                        }

                    }
                }
            }
           
           
            unset($data);
            unset($data2);
            //sort($data3);
            //print_r($data3);die;
            //echo json_encode($data3); die;
            file_put_contents('food.json', json_encode($data3));
            $this->python();
           
            
        }
        
    }
    public function python(){
        file_put_contents('sync.txt', 1);
        echo exec('python3 /var/www/html/cms/api/audio_auto_generate.py');
        file_put_contents('sync.txt', "");
        $this->query("update hotels set add_date = now() WHERE 	hotel_id = 1 ");
        die;
    }
    
    
}
/*
http://localhost/asterisk/api/?function=getlist&extension=4444
http://localhost/nokia/api2/?function=substep&token=n6HhZWvB&substep_id=10101&status=done
http://localhost/nokia/api2/?function=mainstep&token=xDZu58Hs&step_id=2&status=done

https://qa.smacar.com/nokia/api2/?function=loginuser&emp_id=1004&station_id=station1
https://qa.smacar.com/nokia/api2/?function=substep&token=xei2sbaV&substep_id=10102&status=done
https://qa.smacar.com/nokia/api2/?function=mainstep&token=b1iboodU&step_id=1&status=done
*/
