<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
ini_set('max_execution_time', 0);

require("model.php");
class MyController extends MyModel {
	public function __construct() {
        parent::__construct();
        $time_start = microtime(true);
        $req = $_REQUEST;
        $json = array();

        if(isset($req['function'])){
            if($req['function']=="orderv1"){
                $json = $this->makeOrderV1($req['json']);
            } else if($req['function']=="orderv2"){
                $json = $this->makeOrderV2($req['json'],0);
            } else if($req['function']=="orderv3"){
                $json = $this->makeOrderV3($req['json']);
            } else if($req['function']=="price"){
                $json = $this->price($req['json']);
            } else if($req['function']=="orderv5"){
                $json = $this->makeOrderV5($req['json']);
            } else if($req['function']=="pricev5"){
                $json = $this->priceV5($req['json']);
			} else if($req['function']=="startCall"){
                $json = $this->startCall($req['phone_number']);
                
            } else if($req['function']=="getCallerName"){
                $json = $this->getCallerName($req['phone_number']);
			} else if($req['function']=="setCallerName"){
                $json = $this->setCallerName($req['phone_number'],$req['caller_name']);
            } else if($req['function']=="calog"){
                $this->calog2db();
                die;
            } else if($req['function']=="getJson"){
                $this->getJson();
                die;
            } else if($req['function']=="getinventory"){
                $this->getinventory();
            } else if($req['function']=="cloverorder"){
                $this->cloverorder();
            } else if($req['function']=="orderstatus"){
                $this->orderstatus();
			} else if($req['function']=="callforward"){
                $json = $this->makeOrderV5($req['json'],$callforward=1);
            }  else if($req['function']=="python"){
                $this->python();
            }
        } else {
            $json = array('auth'=>0, 'status'=>false, 'msg'=>'Invalid Request'); 
        }
        $time_end = microtime(true);
        $json['time']= ($time_end - $time_start);
        
        if(isset($req['json'])){
            $req['json'] = json_decode($req['json'],true);
        }
        $resp = json_encode($json);
        file_put_contents('log.txt', "\n\n".date('d-m-y H:i:s')."\n".json_encode($req)."\n".$resp.PHP_EOL, FILE_APPEND);
        

		echo $resp;
    }
    
    
    
}

$tis = new MyController();
/*
CREATE TABLE cart_master LIKE `order_master`;
CREATE TABLE cart_details LIKE `order_details`;
ALTER TABLE `cart_master` ADD `org_order_id` INT NOT NULL AFTER `special_note`;
*/