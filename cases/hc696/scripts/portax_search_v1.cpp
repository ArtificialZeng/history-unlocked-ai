#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;
struct Pair { int a,b,col; };
array<array<array<array<int,2>,26>,26>,13> lut;
pair<int,int> slide_pair(int a,int b,int t) {
    int x=(a<13)?a:(a-13-t+13)%13;
    int y=(b/2-t+13)%13;
    if(x==y) return {(a<13)?13+(x+t)%13:x,b^1};
    return {(a<13)?y:13+b/2,2*((x+t)%13)+b%2};
}
vector<Pair> packing(int n,int p) {
    if(n%2) throw runtime_error("even ciphertext length required; no implicit padding");
    vector<Pair> out;
    for(int start=0;start<n;start+=2*p) {
        int h=min(2*p,n-start)/2;
        for(int j=0;j<h;j++)out.push_back({start+j,start+h+j,j});
    }
    return out;
}
string decode(const string& text,const vector<int>& k,const vector<Pair>& pairs) {
    string out(text.size(),' ');
    for(auto q:pairs) {
        auto z=lut[k[q.col]][text[q.a]-'A'][text[q.b]-'A'];
        out[q.a]='A'+z[0];out[q.b]='A'+z[1];
    }
    return out;
}
double score(const string& s,const vector<float>& gram) {
    if(s.size()<4)return 0;
    int n=0;double v=0;
    for(size_t i=0;i<s.size();i++) {
        n=(n*26+s[i]-'A')%(26*26*26*26);
        if(i>=3)v+=gram[n];
    }
    return v;
}
string key_label(const vector<int>&k) {
    string out;for(auto t:k)out+='A'+2*t;return out;
}
int main(int argc,char**argv) {
    if(argc!=6){cerr<<"usage: search model.bin cases.tsv output.tsv restarts seed\n";return 2;}
    vector<float> gram(26*26*26*26);ifstream mod(argv[1],ios::binary);
    if(!mod.read(reinterpret_cast<char*>(gram.data()),gram.size()*sizeof(float)))throw runtime_error("bad model");
    for(int t=0;t<13;t++)for(int a=0;a<26;a++)for(int b=0;b<26;b++) {
        auto z=slide_pair(a,b,t);lut[t][a][b]={z.first,z.second};
        auto q=slide_pair(z.first,z.second,t);
        if(q!=make_pair(a,b))throw runtime_error("pair reciprocity failure");
    }
    int restarts=stoi(argv[4]);mt19937 gen(stoul(argv[5]));
    ifstream cases(argv[2]);ofstream report(argv[3]);
    if(!cases||!report)throw runtime_error("bad cases/output path");
    report<<"case_id\tperiod\traw_quadgram_score\tparameter_penalised_score\teffective_key_representative\tplaintext\n"<<setprecision(12);
    string line;
    while(getline(cases,line)) {
        auto sep=line.find('\t');if(sep==string::npos)throw runtime_error("bad case row");
        string id=line.substr(0,sep),ct=line.substr(sep+1);
        if(!all_of(ct.begin(),ct.end(),[](char c){return c>='A'&&c<='Z';}))throw runtime_error("nonletter input");
        for(int p=1;p<=20;p++) {
            auto pairs=packing(ct.size(),p);map<string,pair<double,string>> unique;
            for(int r=0;r<restarts;r++) {
                vector<int> k(p),cols(p);
                for(int j=0;j<p;j++){k[j]=gen()%13;cols[j]=j;}
                string plain=decode(ct,k,pairs);double v=score(plain,gram);
                for(int pass=0;pass<60;pass++) {
                    bool change=false;shuffle(cols.begin(),cols.end(),gen);
                    for(int j:cols) {
                        int old=k[j],best=old;double bv=v;string bp=plain;
                        for(int t=0;t<13;t++)if(t!=old) {
                            k[j]=t;string test=decode(ct,k,pairs);double tv=score(test,gram);
                            if(tv>bv+1e-7){bv=tv;best=t;bp=test;}
                        }
                        k[j]=best;
                        if(best!=old){change=true;v=bv;plain=bp;}
                    }
                    if(!change)break;
                }
                unique[key_label(k)]={v,plain};
            }
            vector<pair<string,pair<double,string>>> ranked(unique.begin(),unique.end());
            sort(ranked.begin(),ranked.end(),[](auto&a,auto&b){if(a.second.first!=b.second.first)return a.second.first>b.second.first;return a.first<b.first;});
            for(size_t i=0;i<min(size_t(10),ranked.size());i++) {
                auto&[k,row]=ranked[i];
                report<<id<<'\t'<<p<<'\t'<<row.first<<'\t'<<row.first-p*log(13)<<'\t'<<k<<'\t'<<row.second<<'\n';
            }
        }
        report.flush();cerr<<"completed "<<id<<'\n';
    }
}
